from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, Referral
from app.schemas import ReferralDetailsResponse, ReferralHistoryItem
from app.core.security import get_current_user

router = APIRouter(prefix="/referral", tags=["referral"])

@router.get("/details", response_model=ReferralDetailsResponse)
def get_referral_details(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    referral_records = (
        db.query(Referral)
        .filter(Referral.referrer_id == current_user.id)
        .all()
    )
    
    referral_list = []
    bonus_earned = 0.0
    for rec in referral_records:
        referred_user = db.query(User).filter(User.id == rec.referred_user_id).first()
        if referred_user:
            referral_list.append(
                ReferralHistoryItem(
                    referred_user_name=referred_user.name or referred_user.phone[:6] + "****",
                    referred_user_phone=referred_user.phone[:3] + "****" + referred_user.phone[-3:] if len(referred_user.phone) >= 6 else referred_user.phone,
                    bonus_given=rec.bonus_given,
                    created_at=rec.created_at
                )
            )
            if rec.bonus_given:
                bonus_earned += 50.0 # 50 rupees per successful referral conversion
                
    return ReferralDetailsResponse(
        referral_code=current_user.referral_code,
        referral_count=len(referral_records),
        bonus_earned=bonus_earned,
        referrals=referral_list
    )
