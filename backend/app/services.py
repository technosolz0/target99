from sqlalchemy.orm import Session
from datetime import datetime, timezone
import threading
from typing import List, Dict, Tuple
from app.models import User, Contest, ContestParticipant, WalletTransaction, Referral

# Thread-safe in-memory Leaderboard Manager mimicking Redis Sorted Sets
class LeaderboardManager:
    def __init__(self):
        self._lock = threading.Lock()
        # Format: {contest_id: {user_id: (score, timestamp, user_name)}}
        self._scores: Dict[int, Dict[int, Tuple[int, datetime, str]]] = {}

    def update_score(self, contest_id: int, user_id: int, name: str, score: int):
        with self._lock:
            if contest_id not in self._scores:
                self._scores[contest_id] = {}
            self._scores[contest_id][user_id] = (score, datetime.now(timezone.utc), name)

    def get_leaderboard(self, contest_id: int) -> List[Dict]:
        with self._lock:
            if contest_id not in self._scores:
                return []
            
            # Sort players: highest score first, then earliest timestamp (faster answer)
            sorted_players = sorted(
                self._scores[contest_id].items(),
                key=lambda x: (-x[1][0], x[1][1])
            )
            
            leaderboard = []
            for rank, (u_id, (score, _, name)) in enumerate(sorted_players, start=1):
                leaderboard.append({
                    "user_id": u_id,
                    "name": name,
                    "score": score,
                    "rank": rank
                })
            return leaderboard

    def load_from_db(self, db: Session, contest_id: int):
        # Bootstrap in-memory cache from DB records
        participants = (
            db.query(ContestParticipant)
            .join(User)
            .filter(ContestParticipant.contest_id == contest_id)
            .all()
        )
        with self._lock:
            self._scores[contest_id] = {}
            for p in participants:
                self._scores[contest_id][p.user_id] = (p.score, p.joined_at, p.user.name or p.user.phone)

leaderboard_manager = LeaderboardManager()


class WalletService:
    @staticmethod
    def deduct_entry_fee(db: Session, user: User, entry_fee: float) -> WalletTransaction:
        """
        Deduction Rules:
        - Max 10% of entry fee can be paid using Bonus Wallet.
        - Rest is paid by Deposit Wallet.
        - If Deposit Wallet is insufficient, remainder is paid by Winnings Wallet.
        """
        bonus_limit = entry_fee * 0.10
        bonus_to_deduct = min(user.bonus_balance, bonus_limit)
        remaining_fee = entry_fee - bonus_to_deduct
        
        deposit_to_deduct = min(user.deposit_balance, remaining_fee)
        winnings_to_deduct = remaining_fee - deposit_to_deduct
        
        if winnings_to_deduct > user.winning_balance:
            raise ValueError("Insufficient balance to join contest.")
            
        # Perform deductions
        user.bonus_balance -= bonus_to_deduct
        user.deposit_balance -= deposit_to_deduct
        user.winning_balance -= winnings_to_deduct
        
        # Create transaction record
        transaction = WalletTransaction(
            user_id=user.id,
            type="ENTRY_FEE",
            amount=entry_fee,
            status="SUCCESS"
        )
        db.add(transaction)
        db.commit()
        return transaction

    @staticmethod
    def credit_prize(db: Session, user: User, amount: float) -> WalletTransaction:
        user.winning_balance += amount
        transaction = WalletTransaction(
            user_id=user.id,
            type="PRIZE_WIN",
            amount=amount,
            status="SUCCESS"
        )
        db.add(transaction)
        db.commit()
        
        # Send push notification
        from app.core.notifications import send_push_to_user
        send_push_to_user(
            db,
            user.id,
            title="🏆 Contest Prize Credited!",
            body=f"Congratulations! A prize of ₹{amount:.2f} has been credited to your Winnings wallet."
        )
        
        return transaction

    @staticmethod
    def process_deposit(db: Session, user: User, amount: float) -> WalletTransaction:
        user.deposit_balance += amount
        transaction = WalletTransaction(
            user_id=user.id,
            type="DEPOSIT",
            amount=amount,
            status="SUCCESS"
        )
        db.add(transaction)
        db.commit()
        
        # Send push notification
        from app.core.notifications import send_push_to_user
        send_push_to_user(
            db,
            user.id,
            title="💰 Deposit Successful!",
            body=f"₹{amount:.2f} has been successfully added to your Deposit wallet."
        )
        
        return transaction

    @staticmethod
    def process_withdrawal(db: Session, user: User, amount: float) -> WalletTransaction:
        if user.winning_balance < amount:
            raise ValueError("Insufficient winning balance to withdraw.")
        
        user.winning_balance -= amount
        transaction = WalletTransaction(
            user_id=user.id,
            type="WITHDRAWAL",
            amount=amount,
            status="PENDING"  # Needs admin approval
        )
        db.add(transaction)
        db.commit()
        return transaction


class ReferralService:
    @staticmethod
    def check_and_trigger_referral(db: Session, referred_user: User):
        """
        Triggers when a referred user joins their first contest.
        Referral Flow:
        - Referrer (User A) receives ₹50 bonus
        - Referred user (User B) receives ₹20 bonus
        """
        if not referred_user.referred_by:
            return

        # Check if already processed
        existing_referral = (
            db.query(Referral)
            .filter(Referral.referred_user_id == referred_user.id)
            .first()
        )
        
        if existing_referral and existing_referral.bonus_given:
            return

        # Find referrer
        referrer = db.query(User).filter(User.referral_code == referred_user.referred_by).first()
        if not referrer:
            return

        # Award bonuses
        referrer.bonus_balance += 50.0
        referred_user.bonus_balance += 20.0

        # Create/Update referral record
        if not existing_referral:
            referral = Referral(
                referrer_id=referrer.id,
                referred_user_id=referred_user.id,
                bonus_given=True
            )
            db.add(referral)
        else:
            existing_referral.bonus_given = True

        # Log Transactions
        tx_referrer = WalletTransaction(
            user_id=referrer.id,
            type="REFERRAL_BONUS",
            amount=50.0,
            status="SUCCESS"
        )
        tx_referred = WalletTransaction(
            user_id=referred_user.id,
            type="REFERRAL_BONUS",
            amount=20.0,
            status="SUCCESS"
        )
        db.add(tx_referrer)
        db.add(tx_referred)
        db.commit()

        # Send push notifications
        from app.core.notifications import send_push_to_user
        send_push_to_user(
            db,
            referrer.id,
            title="🎁 Referral Bonus Credited!",
            body=f"Your friend {referred_user.name or referred_user.phone} joined their first contest! ₹50.00 bonus has been credited to your wallet."
        )
        send_push_to_user(
            db,
            referred_user.id,
            title="🎉 Welcome Referral Bonus!",
            body="Thanks for signing up using a referral link! ₹20.00 welcome bonus has been credited to your wallet."
        )
