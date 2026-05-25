from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.models import User, Contest, WalletTransaction
from app.schemas import AdminStatsResponse, UserResponse, ContestCreate, ContestResponse, TransactionResponse
from app.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    
    # Calculate deposits
    total_deposits = (
        db.query(func.sum(WalletTransaction.amount))
        .filter(WalletTransaction.type == "DEPOSIT", WalletTransaction.status == "SUCCESS")
        .scalar()
    ) or 0.0
    
    # Calculate winnings paid out
    total_winnings = (
        db.query(func.sum(WalletTransaction.amount))
        .filter(WalletTransaction.type == "PRIZE_WIN", WalletTransaction.status == "SUCCESS")
        .scalar()
    ) or 0.0
    
    # Calculate entry fees collected
    total_entry_fees = (
        db.query(func.sum(WalletTransaction.amount))
        .filter(WalletTransaction.type == "ENTRY_FEE", WalletTransaction.status == "SUCCESS")
        .scalar()
    ) or 0.0
    
    # Calculate platform revenue
    # Revenue = Entry Fees - Winnings Paid
    total_revenue = total_entry_fees - total_winnings
    
    active_contests = db.query(Contest).filter(Contest.status == "ACTIVE").count()
    
    return AdminStatsResponse(
        total_users=total_users,
        total_revenue=total_revenue,
        total_deposits=total_deposits,
        total_winnings_paid=total_winnings,
        active_contests=active_contests
    )

@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.post("/users/{id}/ban", response_model=UserResponse)
def ban_user(id: int, ban: bool, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_banned = ban
    db.commit()
    db.refresh(user)
    return user

@router.post("/contests", response_model=ContestResponse)
def create_contest(request: ContestCreate, db: Session = Depends(get_db)):
    contest = Contest(
        title=request.title,
        entry_fee=request.entry_fee,
        total_slots=request.total_slots,
        prize_pool=request.prize_pool,
        start_time=request.start_time,
        joined_slots=0,
        status="UPCOMING"
    )
    db.add(contest)
    db.commit()
    db.refresh(contest)
    return contest

@router.get("/withdrawals", response_model=List[TransactionResponse])
def get_withdrawals(db: Session = Depends(get_db)):
    return (
        db.query(WalletTransaction)
        .filter(WalletTransaction.type == "WITHDRAWAL")
        .order_by(WalletTransaction.created_at.desc())
        .all()
    )

@router.post("/withdrawals/{id}/approve", response_model=TransactionResponse)
def approve_withdrawal(id: int, approve: bool, db: Session = Depends(get_db)):
    tx = db.query(WalletTransaction).filter(WalletTransaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    if tx.status != "PENDING":
        raise HTTPException(status_code=400, detail="Transaction has already been processed")
        
    if approve:
        tx.status = "SUCCESS"
    else:
        tx.status = "FAILED"
        # Rollback: Refund the user's winning balance
        user = db.query(User).filter(User.id == tx.user_id).first()
        if user:
            user.winning_balance += tx.amount
            
    db.commit()
    db.refresh(tx)
    return tx
