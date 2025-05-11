from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse
from typing import List
from app.core.db import get_db
from app.core.auth import verify_access_token_from_cookie
from app.schemas.bank import (
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankBalanceCheck
)
from app.models.user_model import BankDetails , User, Wallet, Transaction
from app.utils import generate_vpa, generate_timestamped_transaction_id
from uuid import uuid4
from app.schemas.transection import TransactionRequest
import re

router = APIRouter()

@router.get('/transaction')
async def gettransection(request: Request, token_data: dict = Depends(verify_access_token_from_cookie)):
    print(request)
    templates = request.app.state.templates 
    return templates.TemplateResponse("transaction.html", {"request": request, "message": "Hello from FastAPI!"})

@router.get('/transaction/validate-upi/{upi_id}')
async def validate_upi(
    upi_id: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    pattern = r"^[\w.\-]{2,256}@[a-zA-Z]{2,64}$"
    if not re.match(pattern, upi_id):
        return {"valid": False, "message": "Invalid UPI ID format"}

    user = None
    upi_parts = upi_id.split('@')
    
    if len(upi_parts) != 2:
        return {"valid": False, "message": "Invalid UPI ID format"}

    vpa_user, domain = upi_parts

    if domain.lower() == "wallet":
        wallet = db.query(Wallet).filter(Wallet.vpa == upi_id).first()
        if wallet:
            user = db.query(User).filter(User.id == wallet.user_id).first()
    else:
        bank = db.query(BankDetails).filter(BankDetails.vpa == upi_id).first()
        if bank:
            user = db.query(User).filter(User.id == bank.user_id).first()

    if user:
        return {"valid": True, "exists": True, "name": user.name}
    return {"valid": True, "exists": False}\

@router.get("/transaction/methods")
async def get_payment_methods(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    print('mmmmm',token_data)
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user token")
    print(user_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    banks = db.query(BankDetails).filter(BankDetails.user_id == user_id).all()
    methods = []
    if wallet:
        methods.append( {
            'type' : 'wallet',
            "id": wallet.id,
            "vpa": wallet.vpa,
            "balance": wallet.balance
        } )
    for bank in banks:
        methods.append(
             {
                'type' : 'bank',
                "id": bank.id,
                "bank_name": bank.bank_name,
                "account_number":  f"****{bank.account_number[-4:]}" if len(bank.account_number) >= 4 else bank.account_number,#bank.account_number,
                "ifsc_code": bank.ifsc_code,
                "branch_name": bank.branch_name,
                "vpa": bank.vpa,
                "balance": bank.balance,
                "is_primary": bank.is_primary
            }
        )
    	
    return {
        "success": True,
        "methods": methods
    }
    # return {
    #     "wallet": {
    #         "id": wallet.id,
    #         "vpa": wallet.vpa,
    #         "balance": wallet.balance
    #     } if wallet else None,
    #     "banks": [
    #         {
    #             "id": bank.id,
    #             "bank_name": bank.bank_name,
    #             "account_number": bank.account_number,
    #             "ifsc_code": bank.ifsc_code,
    #             "branch_name": bank.branch_name,
    #             "vpa": bank.vpa,
    #             "balance": bank.balance,
    #             "is_primary": bank.is_primary
    #         } for bank in banks
    #     ]
    # }

@router.post('/transaction/process')
async def process_transaction(
    payload: TransactionRequest,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    sender: User = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not sender:
        raise HTTPException(status_code=401, detail="User not found")

    # Validate amount
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Validate recipient
    receiver: User = db.query(User).filter(User.uupi == payload.payeeUpi).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Payee UPI not found")

    # Determine payment method
    payer_account = payer_ifsc = ""
    payee_account = payee_ifsc = ""

    if payload.paymentMethod == "wallet":
        wallet = sender.wallet
        if not wallet or wallet.pin != int(payload.upiPin):
            raise HTTPException(status_code=400, detail="Invalid wallet PIN")
        if wallet.balance < payload.amount:
            raise HTTPException(status_code=400, detail="Insufficient wallet balance")
        wallet.balance -= payload.amount

        payer_account = wallet.vpa
        payer_ifsc = "WALLET"
    elif payload.paymentMethod == "bank":
        bank = db.query(BankDetails).filter(
            BankDetails.id == payload.bankId,
            BankDetails.user_id == sender.id
        ).first()
        if not bank or bank.upi_pin != payload.upiPin:
            raise HTTPException(status_code=400, detail="Invalid bank PIN")
        if bank.balance < payload.amount:
            raise HTTPException(status_code=400, detail="Insufficient bank balance")
        bank.balance -= payload.amount

        payer_account = bank.account_number
        payer_ifsc = bank.ifsc_code
    else:
        raise HTTPException(status_code=400, detail="Invalid payment method")

    # Credit receiver's wallet
    receiver_wallet = receiver.wallet
    if receiver_wallet:
        receiver_wallet.balance += payload.amount
        payee_account = receiver_wallet.vpa
        payee_ifsc = "WALLET"
    elif receiver.bank_details:
        receiver.bank_details.balance += payload.amount
        payee_account = receiver.bank_details.account_number
        payee_ifsc = receiver.bank_details.ifsc_code
    else:
        raise HTTPException(status_code=500, detail="Payee has no active receiving account")

    # Log transaction
    txn = Transaction(
        transaction_id= generate_timestamped_transaction_id(),
        payer_uupi=sender.uupi,
        payee_uupi=receiver.uupi,
        payer_vpa=payer_account,
        payee_vpa=payee_account,
        amount=payload.amount,
        payer_account=payer_account,
        payer_ifsc=payer_ifsc,
        payee_account=payee_account,
        payee_ifsc=payee_ifsc,
    )

    db.add(txn)
    db.commit()

    return {"success": True}
