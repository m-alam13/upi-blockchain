from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.db import get_db
from app.core.auth import verify_access_token_from_cookie
from app.schemas.wallet import (
    Wallet as WalletSchema,
    WalletBalance,
    WalletAddMoney,
   
    Transaction,
    TransactionCreate,
    TransactionResult,
    WalletCreate
)
from app.models.user_model import (
    Wallet as WalletModel,
    
    Transaction as TransactionModel,
    User
)
from app.utils import generate_vpa

router = APIRouter()

# Helper function to get user from token
async def get_current_user(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/wallet", response_class=HTMLResponse)
async def getwallet(request: Request, token_data: dict = Depends(verify_access_token_from_cookie)):
    print(request)
    templates = request.app.state.templates 
    return templates.TemplateResponse("wallet.html", {"request": request, "message": "Hello from FastAPI!"})
@router.get("/create-wallet", response_class=HTMLResponse)
async def get_create_wallet(request: Request, token_data: dict = Depends(verify_access_token_from_cookie)):
    # print(token_data)
    uupi = token_data.get('uupi') +'@wallet'
    templates = request.app.state.templates 
    return templates.TemplateResponse("create_wallet.html", {"request": request,"upi":uupi, "message": "Hello from FastAPI!"})

@router.post("/create-wallet")
def create_wallet(payload: WalletCreate, db: Session = Depends(get_db), token_data: int = Depends(verify_access_token_from_cookie)):
    # Check if user already has a wallet
    user_id = token_data.get('user_id')
    # return c
    print(payload)
    existing = db.query(WalletModel).filter_by(user_id=user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Wallet already exists")

    wallet = WalletModel(
        user_id=user_id,
        vpa=payload.vpa,
        balance = 1000,
        pin=payload.pin
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)

    return {"message": "Wallet created successfully", "wallet_id": wallet.id}
# Wallet Operations
@router.get("/walletdata", response_model=WalletSchema)
async def get_wallet_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    wallet = db.query(WalletModel).filter(WalletModel.user_id == user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    print(wallet)
    return wallet

@router.post("/wallet/add-money", response_model=WalletBalance)
async def add_money(
    request: WalletAddMoney,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    wallet = db.query(WalletModel).filter(WalletModel.user_id == user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found"
        )
    
    wallet.balance += request.amount
    db.commit()
    db.refresh(wallet)
    
    # Record transaction
    transaction = TransactionModel(
        transaction_id=f"txn_{datetime.now().timestamp()}",
        payer_uupi="system",
        payee_uupi=user.uupi,
        payer_vpa="system@financepal",
        payee_vpa=wallet.vpa,
        amount=request.amount,
        payer_account="SYSTEM_ACCOUNT",
        payer_ifsc="SYSTEM_IFSC",
        payee_account=wallet.vpa,
        payee_ifsc="USER_IFSC",
        timestamp=datetime.now()
    )
    db.add(transaction)
    db.commit()
    
    return {"balance": wallet.balance}

# Bank Operations
# @router.get("/bank-details", response_model=BankDetails)
# async def get_bank_details(
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     bank_details = db.query(BankDetailsModel).filter(BankDetailsModel.user_id == user.id).first()
#     if not bank_details:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Bank details not found"
#         )
#     return bank_details

# @router.post("/bank-details/balance", response_model=BankBalance)
# async def check_bank_balance(
#     request: BankCheckBalance,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     bank_details = db.query(BankDetailsModel).filter(BankDetailsModel.user_id == user.id).first()
#     if not bank_details:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Bank details not found"
#         )
    
#     if bank_details.upi_pin != request.upi_pin:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid UPI PIN"
#         )
    
#     return {"balance": bank_details.balance}

# @router.post("/bank-details", response_model=BankDetailsResponse)
# async def create_bank_details(
#     request: BankDetailsCreate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     existing = db.query(BankDetailsModel).filter(BankDetailsModel.user_id == user.id).first()
#     if existing:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Bank details already exist"
#         )
    
#     vpa = generate_vpa(user.name, request.bank_name)
#     bank_details = BankDetailsModel(
#         user_id=user.id,
#         bank_name=request.bank_name,
#         account_number=request.account_number,
#         ifsc_code=request.ifsc_code,
#         upi_pin=request.upi_pin,
#         vpa=vpa,
#         balance=0.0
#     )
    
#     db.add(bank_details)
#     db.commit()
#     db.refresh(bank_details)
    
#     return bank_details

# Transaction Operations
@router.get("/transactions_details", response_model=List[Transaction])
async def get_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    transactions = db.query(TransactionModel).filter(
        (TransactionModel.payer_uupi == user.uupi) | 
        (TransactionModel.payee_uupi == user.uupi)
    ).order_by(TransactionModel.timestamp.desc()).all()
    print(transactions)
    return transactions

# @router.post("/transactions/send", response_model=TransactionResult)
# async def send_money(
#     request: TransactionCreate,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
#     # Get sender wallet
#     sender_wallet = db.query(WalletModel).filter(WalletModel.user_id == user.id).first()
#     if not sender_wallet:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Wallet not found"
#         )
    
#     # Verify PIN
#     if sender_wallet.pin != request.pin:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid PIN"
#         )
    
#     # Check balance
#     if sender_wallet.balance < request.amount:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Insufficient balance"
#         )
    
#     # Get recipient
#     recipient = db.query(User).filter(User.uupi == request.recipient_uupi).first()
#     if not recipient:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Recipient not found"
#         )
    
#     recipient_wallet = db.query(WalletModel).filter(WalletModel.user_id == recipient.id).first()
#     if not recipient_wallet:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Recipient wallet not found"
#         )
    
#     # Perform transaction
#     sender_wallet.balance -= request.amount
#     recipient_wallet.balance += request.amount
    
#     # Create transaction record
#     transaction = TransactionModel(
#         transaction_id=f"txn_{datetime.now().timestamp()}",
#         payer_uupi=user.uupi,
#         payee_uupi=recipient.uupi,
#         payer_vpa=sender_wallet.vpa,
#         payee_vpa=recipient_wallet.vpa,
#         amount=request.amount,
#         payer_account=sender_wallet.vpa,
#         payer_ifsc="USER_IFSC",
#         payee_account=recipient_wallet.vpa,
#         payee_ifsc="RECIPIENT_IFSC",
#         timestamp=datetime.now()
#     )
    
#     db.add(transaction)
#     db.commit()
#     db.refresh(transaction)
    
#     return {
#         "message": "Transaction successful",
#         "new_balance": sender_wallet.balance,
#         "transaction_id": transaction.transaction_id
#     }