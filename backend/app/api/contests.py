from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from app.core.database import get_db
from app.models import User, Contest, ContestParticipant
from app.schemas import ContestResponse, ContestJoinRequest, SubmitScoreRequest, LeaderboardItem
from app.core.security import get_current_user
from app.services import WalletService, ReferralService, leaderboard_manager
from app.websocket import manager  # We will implement this websocket manager shortly

router = APIRouter(prefix="/contests", tags=["contests"])

@router.get("", response_model=List[ContestResponse])
def get_contests(db: Session = Depends(get_db)):
    # Auto start/complete contests based on time if we want to simulate state transitions
    now = datetime.now()
    contests = db.query(Contest).all()
    for c in contests:
        if c.status == "UPCOMING" and c.start_time <= now:
            c.status = "ACTIVE"
            db.commit()
    return contests

@router.post("/join", response_model=ContestResponse)
def join_contest(
    request: ContestJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contest = db.query(Contest).filter(Contest.id == request.contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found."
        )
    
    if contest.status != "UPCOMING" and contest.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot join contest in '{contest.status}' status."
        )
        
    if contest.joined_slots >= contest.total_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contest is full."
        )
        
    # Check if already joined
    existing = (
        db.query(ContestParticipant)
        .filter(
            ContestParticipant.contest_id == contest.id,
            ContestParticipant.user_id == current_user.id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already joined this contest."
        )
        
    # Deduct entry fee using wallet service rules
    try:
        WalletService.deduct_entry_fee(db, current_user, contest.entry_fee)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    # Add participant
    participant = ContestParticipant(
        contest_id=contest.id,
        user_id=current_user.id,
        score=0,
        rank=0,
        joined_at=datetime.now(timezone.utc)
    )
    db.add(participant)
    
    # Increment joined slots
    contest.joined_slots += 1
    db.commit()
    db.refresh(contest)
    
    # Check if first contest joined by referred user to award referral bonus!
    participation_count = (
        db.query(ContestParticipant)
        .filter(ContestParticipant.user_id == current_user.id)
        .count()
    )
    if participation_count == 1:
        # Trigger referral bonus!
        ReferralService.check_and_trigger_referral(db, current_user)
        db.refresh(current_user)

    # Boot the leaderboard manager for this contest
    leaderboard_manager.update_score(
        contest_id=contest.id,
        user_id=current_user.id,
        name=current_user.name or current_user.phone,
        score=0
    )
    
    return contest

@router.post("/submit-score")
async def submit_score(
    request: SubmitScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contest = db.query(Contest).filter(Contest.id == request.contest_id).first()
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found."
        )
        
    participant = (
        db.query(ContestParticipant)
        .filter(
            ContestParticipant.contest_id == contest.id,
            ContestParticipant.user_id == current_user.id
        )
        .first()
    )
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must join the contest first."
        )
        
    # Save the score
    participant.score = request.score
    db.commit()
    
    # Update in-memory leaderboard
    leaderboard_manager.update_score(
        contest_id=contest.id,
        user_id=current_user.id,
        name=current_user.name or current_user.phone,
        score=request.score
    )
    
    # Recalculate ranks in the DB
    updated_leaderboard = leaderboard_manager.get_leaderboard(contest.id)
    for entry in updated_leaderboard:
        db_participant = (
            db.query(ContestParticipant)
            .filter(
                ContestParticipant.contest_id == contest.id,
                ContestParticipant.user_id == entry["user_id"]
            )
            .first()
        )
        if db_participant:
            db_participant.rank = entry["rank"]
    db.commit()
    
    # Broadcast updated leaderboard to all WebSocket clients listening to this contest
    await manager.broadcast_leaderboard(contest.id, updated_leaderboard)
    
    return {"message": "Score submitted successfully.", "score": request.score}

@router.get("/{id}/leaderboard", response_model=List[LeaderboardItem])
def get_leaderboard(id: int, db: Session = Depends(get_db)):
    leaderboard = leaderboard_manager.get_leaderboard(id)
    if not leaderboard:
        # Try loading from database cache if in-memory is empty
        leaderboard_manager.load_from_db(db, id)
        leaderboard = leaderboard_manager.get_leaderboard(id)
    return leaderboard
