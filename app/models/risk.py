from pydantic import BaseModel, Field
from datetime import date


class Risk(BaseModel):
    risk_category: str
    risk_description: str
    implication: str

    likelihood: int = Field(..., ge=1, le=5, description="1=Very Low, 5=Very High")
    impact: int = Field(..., ge=1, le=5, description="1=Very Low, 5=Very High")

    control_score: int = Field(..., ge=1, le=5)

    residual_likelihood: int = Field(..., ge=1, le=5)
    residual_impact: int = Field(..., ge=1, le=5)

    mitigation_strategy: str
    management_response: str
    responsible_person: str
    due_date: date
    follow_up_status: str