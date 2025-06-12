from pydantic import BaseModel
from typing import Optional

class TransactionRequest(BaseModel):
    payeeUpi: str
    amount: float
    paymentMethod: str  # 'wallet' or 'bank'
    upiPin: str
    bankId: Optional[int] = None
