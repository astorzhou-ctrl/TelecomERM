from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

# ✅ Routers
from app.auth.auth import auth_router
from app.risk.risk import risk_router

# ✅ Database
from app.db import engine, Base

# ✅ Import ALL models (CRITICAL: no from app.models import ...)
import app.models.risk_db
import app.models.user_db
import app.models.audit_db


app = FastAPI(
    title="EcoCash Enterprise Risk Management System",
    description="AI-Powered Enterprise Risk Management Platform for EcoCash Holdings",
    version="1.0.0"
)


# =====================
# ✅ CORS CONFIG
# =====================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================
# ✅ CREATE DATABASE TABLES
# =====================

Base.metadata.create_all(bind=engine)


# =====================
# ✅ CUSTOM OPENAPI (JWT AUTHORIZE BUTTON)
# =====================

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # ✅ Add JWT security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# =====================
# ✅ ROUTES
# =====================

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(risk_router, prefix="/risks", tags=["Risk Management"])


# =====================
# ✅ HOME
# =====================

@app.get("/")
def home():
    return {"message": "EcoCash Enterprise Risk Management System"}