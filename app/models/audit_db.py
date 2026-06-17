from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    risk_id = Column(Integer)
    action = Column(String)
    performed_by = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String)