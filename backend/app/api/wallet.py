from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models import User, WalletTransaction
from app.schemas import UserResponse, DepositRequest, WithdrawalRequest, TransactionResponse
from app.core.security import get_current_user
from app.services import WalletService

router = APIRouter(prefix="/wallet", tags=["wallet"])

@router.post("/deposit", response_model=UserResponse)
def add_money(
    request: DepositRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mocking successful payment gateway callback (e.g. Razorpay/Cashfree)
    WalletService.process_deposit(db, current_user, request.amount)
    db.refresh(current_user)
    return current_user

@router.post("/withdraw", response_model=UserResponse)
def withdraw_money(
    request: WithdrawalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pan = request.pan.strip().upper()
    if len(pan) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN format. Must be a 10-character alphanumeric string."
        )
        
    # Verify KYC status simulation
    if current_user.kyc_status != "VERIFIED":
        current_user.kyc_status = "VERIFIED" # Mock auto-verification for PAN entry
        
    try:
        WalletService.process_withdrawal(db, current_user, request.amount)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    transactions = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc())
        .all()
    )
    return transactions
