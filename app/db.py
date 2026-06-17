from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ✅ Database location
DATABASE_URL = "sqlite:///./erm.db"

# ✅ Engine setup
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ✅ Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ Base model
Base = declarative_base()