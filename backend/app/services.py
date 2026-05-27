from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import threading
from typing import List, Dict, Tuple
from app.models import User, Contest, ContestParticipant, WalletTransaction, Referral, Spin

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


class SpinGameService:
    # 12 Alternating glossy sectors on the real-money casino wheel
    WHEEL_SEGMENTS = [
        {"label": "Lose", "multiplier": 0.0, "type": "LOSE"},
        {"label": "1.1x", "multiplier": 1.1, "type": "WIN"},
        {"label": "Try Again", "multiplier": 0.0, "type": "LOSE"},
        {"label": "1.5x", "multiplier": 1.5, "type": "WIN"},
        {"label": "Better Luck Next Time", "multiplier": 0.0, "type": "LOSE"},
        {"label": "2x", "multiplier": 2.0, "type": "WIN"},
        {"label": "0x", "multiplier": 0.0, "type": "LOSE"},
        {"label": "1x", "multiplier": 1.0, "type": "WIN"},
        {"label": "3x", "multiplier": 3.0, "type": "WIN"},
        {"label": "1.2x", "multiplier": 1.2, "type": "WIN"},
        {"label": "Lose", "multiplier": 0.0, "type": "LOSE"},
        {"label": "5x", "multiplier": 5.0, "type": "WIN"},
    ]

    MULTIPLIER_MAP = {
        "Lose": 0.0,
        "0x": 0.0,
        "Better Luck Next Time": 0.0,
        "Try Again": 0.0,
        "1x": 1.0,
        "1.1x": 1.1,
        "1.2x": 1.2,
        "1.5x": 1.5,
        "2x": 2.0,
        "3x": 3.0,
        "5x": 5.0
    }

    # In-memory idempotency check to prevent duplicate spins within 5 seconds
    _processed_idempotency_keys = {}
    _idempotency_lock = threading.Lock()
    _maintenance_mode = False

    @classmethod
    def set_maintenance_mode(cls, enabled: bool):
        cls._maintenance_mode = enabled

    @classmethod
    def is_maintenance_mode(cls) -> bool:
        return cls._maintenance_mode

    @classmethod
    def execute_spin(
        cls,
        db: Session,
        user_id: int,
        bet_amount: float,
        idempotency_key: str,
        device_id: str = None,
        ip_address: str = None
    ) -> Spin:
        if cls._maintenance_mode:
            raise ValueError("Spin Wheel is currently under maintenance. Please try again later.")

        # Check KYC status
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found.")
        if user.is_banned:
            raise ValueError("User account is banned.")
        if user.kyc_status == "REJECTED":
            raise ValueError("KYC has been rejected. Game access restricted.")

        # Check daily responsible gaming limits (Max ₹5000 bet per day)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        from app.models import Spin as SpinModel, SpinAuditLog as AuditLogModel
        daily_bet_sum = (
            db.query(func.sum(SpinModel.bet_amount))
            .filter(SpinModel.user_id == user_id, SpinModel.created_at >= today_start)
            .scalar()
        ) or 0.0
        if daily_bet_sum + bet_amount > 5000.0:
            raise ValueError("Daily gaming limit reached (₹5000). Keep gaming responsible!")

        # 1. Thread-safe duplicate check using idempotency key
        with cls._idempotency_lock:
            now = datetime.now(timezone.utc)
            if idempotency_key in cls._processed_idempotency_keys:
                last_time = cls._processed_idempotency_keys[idempotency_key]
                if (now - last_time).total_seconds() < 5:
                    raise ValueError("Duplicate spin request detected. Please wait.")
            cls._processed_idempotency_keys[idempotency_key] = now

            # Clean up old keys (older than 10 seconds) to prevent memory leak
            keys_to_delete = [
                k for k, t in cls._processed_idempotency_keys.items()
                if (now - t).total_seconds() > 10
            ]
            for k in keys_to_delete:
                del cls._processed_idempotency_keys[k]

        # 2. Concurrency-safe Wallet lock inside transactional context
        # Lock user record to prevent race conditions (double spending)
        locked_user = (
            db.query(User)
            .filter(User.id == user_id)
            .with_for_update()
            .first()
        )

        # Wallet Deduction: Max 20% bonus balance, rest from Deposit -> Winnings
        bonus_limit = bet_amount * 0.20
        bonus_to_deduct = min(locked_user.bonus_balance, bonus_limit)
        remaining_fee = bet_amount - bonus_to_deduct

        deposit_to_deduct = min(locked_user.deposit_balance, remaining_fee)
        winnings_to_deduct = remaining_fee - deposit_to_deduct

        if winnings_to_deduct > locked_user.winning_balance:
            raise ValueError("Insufficient wallet balance for this bet.")

        # Deduct wallet
        locked_user.bonus_balance -= bonus_to_deduct
        locked_user.deposit_balance -= deposit_to_deduct
        locked_user.winning_balance -= winnings_to_deduct

        # Record spin charge transaction
        tx_deduct = WalletTransaction(
            user_id=user_id,
            type="ENTRY_FEE",
            amount=bet_amount,
            status="SUCCESS"
        )
        db.add(tx_deduct)

        # 3. Dynamic weighted random result selection
        from app.models import RTPSettings
        import json
        rtp = (
            db.query(RTPSettings)
            .filter(
                RTPSettings.min_amount <= bet_amount,
                RTPSettings.max_amount >= bet_amount,
                RTPSettings.enabled == True
            )
            .first()
        )

        if rtp:
            weights = json.loads(rtp.probability_json)
        else:
            # Fallback to standard specifications
            if bet_amount < 50:
                weights = {"Lose": 20.0, "1x": 20.0, "1.1x": 18.0, "1.2x": 15.0, "1.5x": 12.0, "2x": 8.0, "3x": 5.0, "5x": 2.0}
            elif bet_amount <= 100:
                weights = {"Lose": 45.0, "1x": 20.0, "1.1x": 15.0, "1.2x": 8.0, "1.5x": 6.0, "2x": 4.0, "3x": 1.5, "5x": 0.5}
            else:
                weights = {"Lose": 65.0, "1x": 15.0, "1.1x": 10.0, "1.2x": 5.0, "1.5x": 3.0, "2x": 1.5, "3x": 0.4, "5x": 0.1}

        outcomes = list(weights.keys())
        probabilities = list(weights.values())

        import random
        chosen_outcome = random.choices(outcomes, weights=probabilities, k=1)[0]
        multiplier = cls.MULTIPLIER_MAP.get(chosen_outcome, 0.0)

        # Find matching segment indices on physical wheel
        matching_segments = [
            (idx, seg) for idx, seg in enumerate(cls.WHEEL_SEGMENTS)
            if (multiplier == 0.0 and seg["type"] == "LOSE") or (multiplier > 0.0 and seg["multiplier"] == multiplier)
        ]
        
        # Pick one at random to offer visual segment diversity (e.g. Try Again vs Better Luck)
        segment_index, chosen_segment = random.choice(matching_segments)
        win_amount = bet_amount * multiplier

        # 4. Auto-credit winnings on positive multipliers
        if win_amount > 0:
            locked_user.winning_balance += win_amount
            tx_win = WalletTransaction(
                user_id=user_id,
                type="PRIZE_WIN",
                amount=win_amount,
                status="SUCCESS"
            )
            db.add(tx_win)

        # 5. Save Spin details
        spin = SpinModel(
            user_id=user_id,
            bet_amount=bet_amount,
            multiplier=multiplier,
            win_amount=win_amount,
            result_type="WIN" if win_amount > 0 else "LOSE",
            wheel_segment=chosen_segment["label"]
        )
        db.add(spin)
        db.flush() # Populate spin.id

        # 6. Save Audit Logs
        audit = AuditLogModel(
            user_id=user_id,
            request_payload=json.dumps({
                "bet_amount": bet_amount,
                "idempotency_key": idempotency_key,
                "device_id": device_id
            }),
            generated_result=json.dumps({
                "spin_id": spin.id,
                "multiplier": multiplier,
                "win_amount": win_amount,
                "segment_index": segment_index,
                "segment_label": chosen_segment["label"]
            }),
            ip_address=ip_address,
            device_id=device_id
        )
        db.add(audit)

        db.commit()

        # Add physical segment index parameter for API response mappings
        spin.segment_index = segment_index
        spin.updated_balance = locked_user.winning_balance + locked_user.deposit_balance + locked_user.bonus_balance

        # Send push notification for significant wins (>3x)
        if multiplier >= 3.0:
            from app.core.notifications import send_push_to_user
            send_push_to_user(
                db,
                user_id,
                title="🔥 JACKPOT SPIN WINNER!",
                body=f"Whoa! You spun the wheel and hit a massive {multiplier}x! ₹{win_amount:.2f} credited instantly."
            )

        return spin


class ContestService:
    @staticmethod
    def complete_contest(db: Session, contest_id: int) -> dict:
        import json
        from app.models import Contest, ContestParticipant, User
        from app.services import WalletService
        from app.core.notifications import send_push_to_user

        contest = db.query(Contest).filter(Contest.id == contest_id).first()
        if not contest:
            return {"error": "Contest not found"}
            
        if contest.status == "COMPLETED":
            return {"message": "Contest is already completed", "payouts": 0}
            
        contest.status = "COMPLETED"
        db.commit()
        
        # Query participants ordered by rank
        participants = (
            db.query(ContestParticipant)
            .filter(ContestParticipant.contest_id == contest_id)
            .order_by(ContestParticipant.rank.asc())
            .all()
        )
        
        if not participants:
            return {"message": "Contest completed with 0 participants.", "payouts": 0}
            
        # Standard rank-based prize pool distribution
        payout_pcts = {1: 0.50, 2: 0.30, 3: 0.20}
        if len(participants) == 1:
            payout_pcts = {1: 1.0}
        elif len(participants) == 2:
            payout_pcts = {1: 0.60, 2: 0.40}
            
        rules = []
        if contest.prize_rules:
            try:
                rules = json.loads(contest.prize_rules)
            except Exception:
                pass
                
        payouts_made = 0
        for p in participants:
            user = db.query(User).filter(User.id == p.user_id).first()
            if not user:
                continue
                
            payout_amount = 0.0
            if rules:
                for rule in rules:
                    min_r = rule.get("min_rank")
                    max_r = rule.get("max_rank")
                    prize = rule.get("prize", 0.0)
                    if min_r <= p.rank <= max_r:
                        payout_amount = float(prize)
                        break
            else:
                if p.rank in payout_pcts:
                    payout_amount = contest.prize_pool * payout_pcts[p.rank]
                    
            if payout_amount > 0:
                WalletService.credit_prize(db, user, payout_amount)
                payouts_made += 1
            else:
                send_push_to_user(
                    db,
                    user.id,
                    title="🏁 Contest Finished!",
                    body=f"Contest '{contest.title}' is completed. You finished at Rank {p.rank}. Better luck next time!"
                )
                
        db.commit()
        return {"message": f"Contest completed. {payouts_made} winners paid out.", "payouts": payouts_made}


