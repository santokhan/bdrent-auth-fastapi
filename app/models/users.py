from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.db import Base

now = datetime.now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False,index=True)
    name = Column(String, nullable=False, index=True)

    username = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=True)

    verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)
