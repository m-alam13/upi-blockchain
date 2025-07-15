from sqlalchemy import Column, Integer, Float, String
from app.core.db import Base
import time

class Block(Base):
    __tablename__ = "blockchain"

    id = Column(Integer, primary_key=True, index=True)
    index = Column(Integer, nullable=False)
    timestamp = Column(Float, default=lambda: time.time())  #  Fix: Use lambda to call at insert time
    data = Column(String(1000))  # Ensure length
    previous_hash = Column(String(128), nullable=False)
    nonce = Column(Integer, nullable=False)
    hash = Column(String(128), nullable=False)
    signature = Column(String(1000))
