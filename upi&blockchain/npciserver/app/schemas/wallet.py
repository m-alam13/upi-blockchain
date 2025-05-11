from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Wallet Schemas
class WalletBase(BaseModel):
    user_id: int

class Wallet(WalletBase):
    balance: float
    pin: str
    vpa: str
    
    class Config:
        orm_mode = True

class WalletAddMoney(BaseModel):
    amount: float
    method: str

class WalletBalance(BaseModel):
    balance: float

class WalletChangePin(BaseModel):
    current_pin: str
    new_pin: str

# Bank Schemas

# Transaction Schemas
class TransactionBase(BaseModel):
    payer_uupi: str
    payee_uupi: str
    amount: float

class TransactionCreate(BaseModel):
    recipient_uupi: str
    amount: float
    pin: str

class Transaction(TransactionBase):
    transaction_id: str
    payer_vpa: str
    payee_vpa: str
    payer_account: str
    payer_ifsc: str
    payee_account: str
    payee_ifsc: str
    timestamp: datetime
    
    class Config:
        orm_mode = True

class TransactionResult(BaseModel):
    message: str
    new_balance: float
    transaction_id: str