from sqlalchemy.orm import Session
from app.models import User

def seed_test_users(db: Session):
    # Check if users already exist in the database
    if db.query(User).count() > 0:
        return

    test_users = [
        User(
            name="Aarav Sharma",
            phone="9876543210",
            email="aarav.sharma@example.com",
            referral_code="T99_AARA",
            referred_by=None,
            deposit_balance=500.0,
            winning_balance=250.0,
            bonus_balance=100.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Aditya Verma",
            phone="9876543211",
            email="aditya.verma@example.com",
            referral_code="T99_ADIT",
            referred_by="T99_AARA",
            deposit_balance=100.0,
            winning_balance=50.0,
            bonus_balance=50.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Ananya Iyer",
            phone="9876543212",
            email="ananya.iyer@example.com",
            referral_code="T99_ANAN",
            referred_by="T99_AARA",
            deposit_balance=0.0,
            winning_balance=0.0,
            bonus_balance=20.0,
            kyc_status="PENDING",
            is_banned=False
        ),
        User(
            name="Vikram Malhotra",
            phone="9876543213",
            email="vikram.m@example.com",
            referral_code="T99_VIKR",
            referred_by=None,
            deposit_balance=1000.0,
            winning_balance=1200.0,
            bonus_balance=300.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Rohan Gupta",
            phone="9876543214",
            email="rohan.g@example.com",
            referral_code="T99_ROHA",
            referred_by=None,
            deposit_balance=200.0,
            winning_balance=0.0,
            bonus_balance=10.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Diya Kapoor",
            phone="9876543215",
            email="diya.k@example.com",
            referral_code="T99_DIYA",
            referred_by=None,
            deposit_balance=50.0,
            winning_balance=10.0,
            bonus_balance=0.0,
            kyc_status="PENDING",
            is_banned=False
        ),
        User(
            name="Ishaan Sen",
            phone="9876543216",
            email="ishaan.s@example.com",
            referral_code="T99_ISHA",
            referred_by="T99_VIKR",
            deposit_balance=1500.0,
            winning_balance=450.0,
            bonus_balance=150.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Meera Nair",
            phone="9876543217",
            email="meera.n@example.com",
            referral_code="T99_MEER",
            referred_by=None,
            deposit_balance=0.0,
            winning_balance=0.0,
            bonus_balance=0.0,
            kyc_status="REJECTED",
            is_banned=False
        ),
        User(
            name="Kabir Mehta",
            phone="9876543218",
            email="kabir.m@example.com",
            referral_code="T99_KABI",
            referred_by=None,
            deposit_balance=350.0,
            winning_balance=75.0,
            bonus_balance=25.0,
            kyc_status="VERIFIED",
            is_banned=False
        ),
        User(
            name="Neha Sharma",
            phone="9876543219",
            email="neha.s@example.com",
            referral_code="T99_NEHA",
            referred_by="T99_KABI",
            deposit_balance=50.0,
            winning_balance=0.0,
            bonus_balance=10.0,
            kyc_status="PENDING",
            is_banned=False
        )
    ]

    db.bulk_save_objects(test_users)
    db.commit()
