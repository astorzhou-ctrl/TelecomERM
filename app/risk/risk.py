from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.responses import FileResponse

from app.models.risk import Risk
from app.db import SessionLocal
from app.models.risk_db import RiskDB
from app.models.audit_db import AuditLog   # ✅ ADDED
from app.auth.auth import get_current_user, require_role  # ✅ UPDATED

from openpyxl import Workbook
from datetime import datetime

# ✅ MUST BE FIRST
risk_router = APIRouter()


# =====================
# UTIL FUNCTIONS
# =====================

def calculate_rating(score: int):
    if score >= 11:
        return "High"
    elif score >= 8:
        return "Medium"
    else:
        return "Low"


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
# CREATE RISK
# =====================

@risk_router.post("/")
def create_risk(risk: Risk, user: dict = Depends(get_current_user)):
    db = SessionLocal()

    if risk.control_score < 1 or risk.control_score > 5:
        db.close()
        raise HTTPException(
            status_code=400,
            detail="control_score must be between 1 and 5"
        )

    db_risk = RiskDB(
        risk_category=risk.risk_category,
        risk_description=risk.risk_description,
        implication=risk.implication,
        likelihood=risk.likelihood,
        impact=risk.impact,
        inherent_risk_score=risk.likelihood * risk.impact,
        inherent_rating=calculate_rating(risk.likelihood * risk.impact),
        control_score=risk.control_score,
        control_rating=control_rating(risk.control_score),
        residual_likelihood=risk.residual_likelihood,
        residual_impact=risk.residual_impact,
        residual_risk_score=risk.residual_likelihood * risk.residual_impact,
        residual_rating=calculate_rating(risk.residual_likelihood * risk.residual_impact),
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
    audit = AuditLog(
        risk_id=db_risk.id,
        action="CREATE",
        performed_by=user["sub"],
        details=f"Created risk: {db_risk.risk_description}"
    )
    db.add(audit)
    db.commit()

    db.close()

    return db_risk


# =====================
# UPDATE RISK
# =====================

@risk_router.put("/{risk_id}")
def update_risk(risk_id: int, updated_data: Risk, user: dict = Depends(get_current_user)):
    db = SessionLocal()

    db_risk = db.query(RiskDB).filter(RiskDB.id == risk_id).first()

    if not db_risk:
        db.close()
        raise HTTPException(status_code=404, detail="Risk not found")

    db_risk.risk_category = updated_data.risk_category
    db_risk.risk_description = updated_data.risk_description
    db_risk.implication = updated_data.implication
    db_risk.likelihood = updated_data.likelihood
    db_risk.impact = updated_data.impact

    db_risk.inherent_risk_score = updated_data.likelihood * updated_data.impact
    db_risk.inherent_rating = calculate_rating(db_risk.inherent_risk_score)

    db_risk.control_score = updated_data.control_score
    db_risk.control_rating = control_rating(updated_data.control_score)

    db_risk.residual_likelihood = updated_data.residual_likelihood
    db_risk.residual_impact = updated_data.residual_impact
    db_risk.residual_risk_score = updated_data.residual_likelihood * updated_data.residual_impact
    db_risk.residual_rating = calculate_rating(db_risk.residual_risk_score)

    db_risk.mitigation_strategy = updated_data.mitigation_strategy
    db_risk.management_response = updated_data.management_response
    db_risk.responsible_person = updated_data.responsible_person
    db_risk.due_date = updated_data.due_date
    db_risk.follow_up_status = updated_data.follow_up_status

    db_risk.updated_by = user["sub"]
    db_risk.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_risk)

    # ✅ AUDIT LOG
    audit = AuditLog(
        risk_id=db_risk.id,
        action="UPDATE",
        performed_by=user["sub"],
        details=f"Updated risk: {db_risk.risk_description}"
    )
    db.add(audit)
    db.commit()

    db.close()

    return db_risk


# =====================
# DELETE RISK (ADMIN ONLY)
# =====================

@risk_router.delete("/{risk_id}")
def delete_risk(
    risk_id: int,
    user: dict = Depends(require_role(["admin"]))
):
    db = SessionLocal()

    db_risk = db.query(RiskDB).filter(RiskDB.id == risk_id).first()

    if not db_risk:
        db.close()
        raise HTTPException(status_code=404, detail="Risk not found")

    db.delete(db_risk)
    db.commit()

    # ✅ AUDIT LOG
    audit = AuditLog(
        risk_id=risk_id,
        action="DELETE",
        performed_by=user["sub"],
        details="Deleted risk"
    )
    db.add(audit)
    db.commit()

    db.close()

    return {"message": "Risk deleted successfully"}


# =====================
# GET RISKS
# =====================

@risk_router.get("/")
def get_risks():
    db = SessionLocal()
    risks = db.query(RiskDB).all()
    db.close()
    return risks


# =====================
# GET AUDIT LOGS ✅
# =====================

@risk_router.get("/audit")
def get_audit_logs():
    db = SessionLocal()
    logs = db.query(AuditLog).all()
    db.close()
    return logs


# =====================
# SUMMARY
# =====================

@risk_router.get("/summary")
def get_summary():
    db = SessionLocal()
    risks = db.query(RiskDB).all()

    result = {
        "total_risks": len(risks),
        "high_risks": len([r for r in risks if r.inherent_rating == "High"]),
        "medium_risks": len([r for r in risks if r.inherent_rating == "Medium"]),
        "low_risks": len([r for r in risks if r.inherent_rating == "Low"])
    }

    db.close()
    return result


# =====================
# HEATMAP
# =====================

@risk_router.get("/heatmap")
def heatmap():
    db = SessionLocal()
    risks = db.query(RiskDB).all()

    result = [
        {"likelihood": r.likelihood, "impact": r.impact, "rating": r.inherent_rating}
        for r in risks
    ]

    db.close()
    return result


# =====================
# EXPORT
# =====================

@risk_router.get("/export")
def export(search: str = Query(None), rating: str = Query(None)):
    db = SessionLocal()
    risks = db.query(RiskDB).all()

    if search:
        s = search.lower()
        risks = [
            r for r in risks
            if s in r.risk_category.lower()
            or s in r.risk_description.lower()
        ]

    if rating:
        risks = [r for r in risks if r.inherent_rating == rating]

    wb = Workbook()
    ws = wb.active
    ws.title = "Risks"

    ws.append([
        "ID", "Category", "Description", "Score", "Rating",
        "Owner", "Created By", "Updated By"
    ])

    for r in risks:
        ws.append([
            r.id,
            r.risk_category,
            r.risk_description,
            r.inherent_risk_score,
            r.inherent_rating,
            r.responsible_person,
            r.created_by,
            r.updated_by
        ])

    file_path = "risks.xlsx"
    wb.save(file_path)

    db.close()

    return FileResponse(file_path)