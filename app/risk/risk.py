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
    ws.title = "Risk Register"

    # ✅ FULL HEADERS (MATCH YOUR TEMPLATE)
    headers = [
        "Risk ID",
        "Risk Category",
        "Risk Description",
        "Implication",
        "Likelihood",
        "Impact",
        "Inherent Risk Score",
        "Risk Impact",
        "Inherent Risk Rating",
        "Control Score",
        "Internal Control Rating",
        "Residual Likelihood",
        "Residual Impact",
        "Residual Risk Score",
        "Residual Risk Impact",
        "Proposed Mitigation/Strategies",
        "Management Response",
        "Responsible Person",
        "Due Date",
        "Follow Up Status"
    ]

    ws.append(headers)

    for r in risks:
        ws.append([
            r.id,
            r.risk_category,
            r.risk_description,
            r.implication,
            r.likelihood,
            r.impact,
            r.inherent_risk_score,
            r.inherent_rating,
            r.inherent_rating,  # can refine later
            r.control_score,
            r.control_rating,
            r.residual_likelihood,
            r.residual_impact,
            r.residual_risk_score,
            r.residual_rating,
            r.mitigation_strategy,
            r.management_response,
            r.responsible_person,
            r.due_date,
            r.follow_up_status
        ])

    file_path = "risk_register.xlsx"
    wb.save(file_path)

    db.close()

    return FileResponse(file_path, filename="Risk_Register.xlsx")