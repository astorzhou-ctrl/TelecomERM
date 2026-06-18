from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import FileResponse

from app.models.risk import Risk
from app.db import SessionLocal
from app.models.risk_db import RiskDB
from app.models.audit_db import AuditLog
from app.auth.auth import get_current_user, require_role

from openpyxl import Workbook
from datetime import datetime

# ✅ FIXED: Router defined FIRST
risk_router = APIRouter()

# =====================
# UTIL FUNCTIONS
# =====================

def calculate_rating(score: int):
    if score <= 5:
        return "Minor"
    elif score <= 10:
        return "Moderate"
    elif score <= 15:
        return "Significant"
    elif score <= 20:
        return "Severe"
    else:
        return "Catastrophic"


def control_rating(score: int):
    mapping = {
        1: "Strong",
        2: "Reasonably Strong",
        3: "Adequate",
        4: "Marginally Adequate",
        5: "Weak"
    }
    return mapping.get(score, "Unknown")

# =====================
# VALIDATION FUNCTION
# =====================

def validate_scale(value, field):
    if value < 1 or value > 5:
        raise HTTPException(status_code=400, detail=f"{field} must be between 1 and 5")

# =====================
# CREATE RISK
# =====================

@risk_router.post("/")
def create_risk(risk: Risk, user: dict = Depends(get_current_user)):
    db = SessionLocal()

    # ✅ VALIDATION
    validate_scale(risk.likelihood, "Likelihood")
    validate_scale(risk.impact, "Impact")
    validate_scale(risk.residual_likelihood, "Residual likelihood")
    validate_scale(risk.residual_impact, "Residual impact")
    validate_scale(risk.control_score, "Control score")

    inherent_score = risk.likelihood * risk.impact
    residual_score = risk.residual_likelihood * risk.residual_impact

    db_risk = RiskDB(
        risk_category=risk.risk_category,
        risk_description=risk.risk_description,
        implication=risk.implication,
        likelihood=risk.likelihood,
        impact=risk.impact,
        inherent_risk_score=inherent_score,
        inherent_rating=calculate_rating(inherent_score),

        control_score=risk.control_score,
        control_rating=control_rating(risk.control_score),

        residual_likelihood=risk.residual_likelihood,
        residual_impact=risk.residual_impact,
        residual_risk_score=residual_score,
        residual_rating=calculate_rating(residual_score),

        mitigation_strategy=risk.mitigation_strategy,
        management_response=risk.management_response,
        responsible_person=risk.responsible_person,
        due_date=risk.due_date,
        follow_up_status=risk.follow_up_status,

        created_by=user["sub"]
    )

    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)

    # ✅ AUDIT LOG
    db.add(AuditLog(
        risk_id=db_risk.id,
        action="CREATE",
        performed_by=user["sub"],
        details=f"Created risk: {db_risk.risk_description}"
    ))
    db.commit()

    db.close()
    return db_risk

# =====================
# UPDATE RISK
# =====================

@risk_router.put("/{risk_id}")
def update_risk(risk_id: int, updated: Risk, user: dict = Depends(get_current_user)):
    db = SessionLocal()

    db_risk = db.query(RiskDB).filter(RiskDB.id == risk_id).first()

    if not db_risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    # ✅ VALIDATION
    validate_scale(updated.likelihood, "Likelihood")
    validate_scale(updated.impact, "Impact")
    validate_scale(updated.residual_likelihood, "Residual likelihood")
    validate_scale(updated.residual_impact, "Residual impact")
    validate_scale(updated.control_score, "Control score")

    inherent_score = updated.likelihood * updated.impact
    residual_score = updated.residual_likelihood * updated.residual_impact

    db_risk.risk_category = updated.risk_category
    db_risk.risk_description = updated.risk_description
    db_risk.implication = updated.implication

    db_risk.likelihood = updated.likelihood
    db_risk.impact = updated.impact
    db_risk.inherent_risk_score = inherent_score
    db_risk.inherent_rating = calculate_rating(inherent_score)

    db_risk.control_score = updated.control_score
    db_risk.control_rating = control_rating(updated.control_score)

    db_risk.residual_likelihood = updated.residual_likelihood
    db_risk.residual_impact = updated.residual_impact
    db_risk.residual_risk_score = residual_score
    db_risk.residual_rating = calculate_rating(residual_score)

    db_risk.mitigation_strategy = updated.mitigation_strategy
    db_risk.management_response = updated.management_response
    db_risk.responsible_person = updated.responsible_person
    db_risk.due_date = updated.due_date
    db_risk.follow_up_status = updated.follow_up_status

    db_risk.updated_by = user["sub"]
    db_risk.updated_at = datetime.utcnow()

    db.commit()

    # ✅ AUDIT
    db.add(AuditLog(
        risk_id=risk_id,
        action="UPDATE",
        performed_by=user["sub"],
        details="Risk updated"
    ))
    db.commit()

    db.close()
    return db_risk

# =====================
# DELETE
# =====================

@risk_router.delete("/{risk_id}")
def delete_risk(risk_id: int, user: dict = Depends(require_role(["admin"]))):
    db = SessionLocal()

    risk = db.query(RiskDB).filter(RiskDB.id == risk_id).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    db.delete(risk)
    db.commit()

    db.add(AuditLog(
        risk_id=risk_id,
        action="DELETE",
        performed_by=user["sub"],
        details="Deleted risk"
    ))
    db.commit()

    db.close()
    return {"message": "Deleted"}

# =====================
# GET RISKS
# =====================

@risk_router.get("/")
def get_risks():
    db = SessionLocal()
    data = db.query(RiskDB).all()
    db.close()
    return data

# =====================
# AUDIT
# =====================

@risk_router.get("/audit")
def get_audit():
    db = SessionLocal()
    data = db.query(AuditLog).all()
    db.close()
    return data

# =====================
# SUMMARY
# =====================

@risk_router.get("/summary")
def summary():
    db = SessionLocal()
    risks = db.query(RiskDB).all()

    res = {
        "total_risks": len(risks),
        "high": len([r for r in risks if r.inherent_rating == "Catastrophic"]),
        "medium": len([r for r in risks if r.inherent_rating == "Significant"]),
        "low": len([r for r in risks if r.inherent_rating == "Moderate"])
    }

    db.close()
    return res

# =====================
# HEATMAP
# =====================

@risk_router.get("/heatmap")
def heatmap():
    db = SessionLocal()
    data = [
        {"likelihood": r.likelihood, "impact": r.impact}
        for r in db.query(RiskDB).all()
    ]
    db.close()
    return data

# =====================
# EXPORT
# =====================

@risk_router.get("/export")
def export():
    db = SessionLocal()
    risks = db.query(RiskDB).all()

    wb = Workbook()
    ws = wb.active

    # ✅ EXACT HEADERS
    ws.append([
        "Risk ID", "Risk Category", "Risk Description", "Implication",
        "Likelihood", "Impact", "Inherent Score", "Inherent Rating",
        "Control Score", "Control Rating",
        "Residual Likelihood", "Residual Impact", "Residual Score", "Residual Rating",
        "Mitigation Strategy", "Management Response",
        "Responsible Person", "Due Date", "Follow-up Status"
    ])

    for r in risks:
        ws.append([
            r.id, r.risk_category, r.risk_description, r.implication,
            r.likelihood, r.impact, r.inherent_risk_score, r.inherent_rating,
            r.control_score, r.control_rating,
            r.residual_likelihood, r.residual_impact,
            r.residual_risk_score, r.residual_rating,
            r.mitigation_strategy, r.management_response,
            r.responsible_person, str(r.due_date), r.follow_up_status
        ])

    file = "risk_register.xlsx"
    wb.save(file)

    db.close()

    return FileResponse(file, filename="Risk_Register.xlsx")