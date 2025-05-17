from app.core.db import Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean,ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):
    __tablename__ = "kyc_users"

    id = Column(Integer, primary_key=True, index=True)
    pan = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    mobile = Column(String(255), nullable=False)
    uupi = Column(String(255), unique=True, index=True, nullable=True)
    image_path = Column(String(255), nullable=True)  # path to saved image


