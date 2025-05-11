from app.core.db import Base
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Boolean,ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    mobile = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    uupi = Column(String(255), unique=True, index=True, nullable=True)  # ensure uniqueness and index for FK refs

    bank_details = relationship("BankDetails", back_populates="user", uselist=False)
    wallet = relationship("Wallet", back_populates="user", uselist=False)

    transactions_sent = relationship(
        "Transaction",
        back_populates="payer",
        foreign_keys="Transaction.payer_uupi"
    )
    transactions_received = relationship(
        "Transaction",
        back_populates="payee",
        foreign_keys="Transaction.payee_uupi"
    )


class BankDetails(Base):
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bank_name = Column(String(50), nullable=False)
    account_number = Column(String(18), nullable=False)
    account_holder_name = Column(String(100))
    ifsc_code = Column(String(11), nullable=False)
    branch_name = Column(String(50))
    upi_pin = Column(String(6), nullable=False)
    vpa = Column(String(50), nullable=False)
    balance = Column(Float, default=0.0)
    is_primary = Column(Boolean, default=False)

    user = relationship("User", back_populates="bank_details")


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=0.0)
    pin = Column(Integer, nullable=False)
    vpa = Column(String(255), nullable=False)
    user = relationship("User", back_populates="wallet")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, index=True, nullable=False)
    payer_uupi = Column(String(255), ForeignKey("users.uupi"), nullable=False)
    payee_uupi = Column(String(255), ForeignKey("users.uupi"), nullable=False)
    payer_vpa = Column(String(255), unique=True, index=True, nullable=False)
    payee_vpa = Column(String(255), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    payer_account = Column(String(255), nullable=False)
    payer_ifsc = Column(String(255), nullable=False)
    payee_account = Column(String(255), nullable=False)
    payee_ifsc = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    payer = relationship("User", foreign_keys=[payer_uupi], back_populates="transactions_sent")
    payee = relationship("User", foreign_keys=[payee_uupi], back_populates="transactions_received")
