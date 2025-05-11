from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.auth import verify_access_token_from_cookie
from app.schemas.bank import (
    BankAccountCreate,
    BankAccountResponse,
    BankAccountUpdate,
    BankBalanceCheck
)
from app.models.user_model import BankDetails as BankAccount, User
from app.utils import generate_vpa

router = APIRouter(prefix="/bank-accounts", tags=["Bank Accounts"])

@router.post("", response_model=BankAccountResponse)
async def create_bank_account(
    account_data: BankAccountCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Create a new bank account for the authenticated user"""
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate VPA if not provided
    if not account_data.vpa:
        account_data.vpa = generate_vpa(user.name, account_data.bank_name)
    
    # Check for duplicate account number
    existing_account = db.query(BankAccount).filter(
        BankAccount.account_number == account_data.account_number,
        BankAccount.user_id == user.id
    ).first()
    
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bank account with this number already exists"
        )
    
    new_account = BankAccount(
        user_id=user.id,
        **account_data.dict()
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    return new_account

@router.get("", response_model=List[BankAccountResponse])
async def get_user_bank_accounts(
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Get all bank accounts for the authenticated user"""
    accounts = db.query(BankAccount).filter(
        BankAccount.user_id == token_data["user_id"]
    ).all()
    return accounts

@router.get("/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Get specific bank account details"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == token_data["user_id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    return account

@router.put("/{account_id}", response_model=BankAccountResponse)
async def update_bank_account(
    account_id: int,
    update_data: BankAccountUpdate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Update bank account details"""
    print("mmmm")
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == token_data["user_id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    
    return account

@router.delete("/{account_id}")
async def delete_bank_account(
    account_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Delete a bank account"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == token_data["user_id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    db.delete(account)
    db.commit()
    
    return {"message": "Bank account deleted successfully"}

@router.post("/{account_id}/check-balance", response_model=BankBalanceCheck)
async def check_bank_balance(
    account_id: int,
    balance_check: BankBalanceCheck,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Check balance for a specific bank account"""
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == token_data["user_id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    if account.upi_pin != balance_check.upi_pin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid UPI PIN"
        )
    
    return {"balance": account.balance}

@router.post("/{account_id}/set-primary")
async def set_primary_account(
    account_id: int,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_access_token_from_cookie)
):
    """Set a bank account as primary"""
    # First reset all primary flags
    db.query(BankAccount).filter(
        BankAccount.user_id == token_data["user_id"]
    ).update({"is_primary": False})
    
    # Set the selected account as primary
    account = db.query(BankAccount).filter(
        BankAccount.id == account_id,
        BankAccount.user_id == token_data["user_id"]
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank account not found"
        )
    
    account.is_primary = True
    db.commit()
    
    return {"message": "Primary bank account updated successfully"}