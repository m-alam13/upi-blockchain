from pydantic import BaseModel, Field
from typing import Optional

class BankAccountBase(BaseModel):
    bank_name: str = Field(..., min_length=2, max_length=50)
    account_number: str = Field(..., min_length=10, max_length=18)
    ifsc_code: str = Field(..., min_length=8, max_length=11)
    branch_name: Optional[str] = Field(None, max_length=50)
    account_holder_name: Optional[str] = Field(None, max_length=100)

class BankAccountCreate(BankAccountBase):
    upi_pin: str = Field(..., min_length=4, max_length=6)
    vpa: Optional[str] = Field(None, min_length=5, max_length=50)
    balance: float = Field(0.0, ge=0)
    is_primary: bool = Field(False)

class BankAccountUpdate(BaseModel):
    bank_name: Optional[str] = Field(None, min_length=2, max_length=50)
    ifsc_code: Optional[str] = Field(..., min_length=8, max_length=11)
    account_holder_name: Optional[str] = Field(None, max_length=100)
    branch_name: Optional[str] = Field(None, max_length=50)
    upi_pin: Optional[str] = Field(None, min_length=4, max_length=6)
    # is_primary: Optional[bool] = None

class BankAccountResponse(BankAccountBase):
    id: int
    user_id: int
    vpa: str
    balance: float
    is_primary: bool
    
    class Config:
        orm_mode = True

class BankBalanceCheck(BaseModel):
    upi_pin: str = Field(..., min_length=4, max_length=6)