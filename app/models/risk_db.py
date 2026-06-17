from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db import Base


class RiskDB(Base):
    __tablename__ = "risks"

    id = Column(Integer, primary_key=True, index=True)

    risk_category = Column(String)
    risk_description = Column(String)
    implication = Column(String)

    likelihood = Column(Integer)
    impact = Column(Integer)

    inherent_risk_score = Column(Integer)
    inherent_rating = Column(String)

    control_score = Column(Integer)
    control_rating = Column(String)

    residual_likelihood = Column(Integer)
    residual_impact = Column(Integer)

    residual_risk_score = Column(Integer)
    residual_rating = Column(String)

    mitigation_strategy = Column(String)
    management_response = Column(String)
    responsible_person = Column(String)
    due_date = Column(String)
    follow_up_status = Column(String)

    # ✅ AUDIT FIELDS (CREATION)
    created_by = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ✅ AUDIT FIELDS (UPDATES)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())