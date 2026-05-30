import os
import sys
import json
import random
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import FruitContest, ImagePuzzleContest, WordContest, WordQuestion

# --- MOCK IMAGE PUZZLE CONTESTS ---
PUZZLE_CONTESTS = [
    {
        "title": "🧩 Vintage Auto Puzzle Arena",
        "entry_fee": 15.0,
        "total_slots": 50,
        "prize_pool": 600.0,
        "image_url": "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600&auto=format&fit=crop",
        "grid_size": 3,
        "duration_seconds": 240,
        "offset_start_hours": -1,  # Started 1 hour ago (Active)
        "offset_end_hours": 3,
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 250.0},
            {"min_rank": 2, "max_rank": 3, "prize": 100.0},
            {"min_rank": 4, "max_rank": 10, "prize": 20.0}
        ]
    },
    {
        "title": "🚀 Outer Space Odyssey Grid",
        "entry_fee": 40.0,
        "total_slots": 100,
        "prize_pool": 3200.0,
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop",
        "grid_size": 4,
        "duration_seconds": 360,
        "offset_start_hours": 2,  # Starts in 2 hours (Upcoming)
        "offset_end_hours": 5,
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 1500.0},
            {"min_rank": 2, "max_rank": 2, "prize": 800.0},
            {"min_rank": 3, "max_rank": 5, "prize": 300.0}
        ]
    },
    {
        "title": "🏔️ Alpine Summit Speedrun",
        "entry_fee": 100.0,
        "total_slots": 20,
        "prize_pool": 1800.0,
        "image_url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&auto=format&fit=crop",
        "grid_size": 5,
        "duration_seconds": 600,
        "offset_start_hours": -5,  # Finished 2 hours ago (Completed)
        "offset_end_hours": -2,
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 1000.0},
            {"min_rank": 2, "max_rank": 2, "prize": 500.0},
            {"min_rank": 3, "max_rank": 3, "prize": 300.0}
        ]
    }
]

# --- MOCK FRUIT SLICING TOURNAMENTS ---
FRUIT_CONTESTS = [
    {
        "title": "🍍 Citrus Slicer Tournament",
        "entry_fee": 10.0,
        "total_slots": 100,
        "prize_pool": 800.0,
        "duration_seconds": 60,
        "offset_start_hours": -0.5,  # Started 30 mins ago (Active)
        "offset_end_hours": 1.5,
        "seed": "citrus_spawner_seed_99",
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 350.0},
            {"min_rank": 2, "max_rank": 3, "prize": 150.0},
            {"min_rank": 4, "max_rank": 10, "prize": 20.0}
        ]
    },
    {
        "title": "🍉 Watermelon Blast Showdown",
        "entry_fee": 50.0,
        "total_slots": 50,
        "prize_pool": 2200.0,
        "duration_seconds": 60,
        "offset_start_hours": 1.5,  # Starts in 1.5 hours (Upcoming)
        "offset_end_hours": 3.5,
        "seed": "watermelon_spawner_heavy_seed",
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 1000.0},
            {"min_rank": 2, "max_rank": 2, "prize": 600.0},
            {"min_rank": 3, "max_rank": 5, "prize": 200.0}
        ]
    },
    {
        "title": "🍓 Berry Blitz Frenzy",
        "entry_fee": 5.0,
        "total_slots": 200,
        "prize_pool": 850.0,
        "duration_seconds": 45,
        "offset_start_hours": -4,  # Finished 2 hours ago (Completed)
        "offset_end_hours": -2,
        "seed": "strawberry_spawner_berry_seed",
        "prize_rules": [
            {"min_rank": 1, "max_rank": 1, "prize": 300.0},
            {"min_rank": 2, "max_rank": 5, "prize": 100.0},
            {"min_rank": 6, "max_rank": 15, "prize": 15.0}
        ]
    }
]

# --- MOCK WORD PUZZLE CONTESTS & QUESTIONS ---
WORD_CONTESTS_DATA = [
    {
        "contest": {
            "title": "🔤 Technical Vocab Championship",
            "entry_fee": 20.0,
            "total_slots": 80,
            "prize_pool": 1400.0,
            "difficulty": "MEDIUM",
            "duration_seconds": 180,
            "offset_start_hours": -1,  # Active
            "offset_end_hours": 2,
            "prize_rules": [
                {"min_rank": 1, "max_rank": 1, "prize": 600.0},
                {"min_rank": 2, "max_rank": 3, "prize": 250.0},
                {"min_rank": 4, "max_rank": 10, "prize": 40.0}
            ]
        },
        "questions": [
            {
                "game_type": "UNSCRAMBLE",
                "difficulty": "MEDIUM",
                "puzzle_data": {"scrambled": "NOHYTP"},
                "clues": "Popular dynamic programming language used widely for AI and backend.",
                "correct_answer": "PYTHON",
                "points_reward": 100
            },
            {
                "game_type": "MISSING_LETTERS",
                "difficulty": "MEDIUM",
                "puzzle_data": {"pattern": "F_S_A_I"},
                "clues": "High-performance Python web framework used for building APIs.",
                "correct_answer": "FASTAPI",
                "points_reward": 120
            },
            {
                "game_type": "WORD_SEARCH",
                "difficulty": "MEDIUM",
                "puzzle_data": {
                    "grid": [
                        ["P", "Y", "T", "H", "O", "N"],
                        ["X", "F", "L", "U", "T", "T"],
                        ["A", "B", "C", "D", "E", "F"],
                        ["J", "A", "V", "A", "K", "L"]
                    ]
                },
                "clues": "Find the name of the language used to write Android apps (JAVA) in the last row.",
                "correct_answer": "JAVA",
                "points_reward": 100
            }
        ]
    },
    {
        "contest": {
            "title": "🧠 Advanced Crossword Arena",
            "entry_fee": 50.0,
            "total_slots": 30,
            "prize_pool": 1350.0,
            "difficulty": "HARD",
            "duration_seconds": 300,
            "offset_start_hours": 3,  # Upcoming
            "offset_end_hours": 6,
            "prize_rules": [
                {"min_rank": 1, "max_rank": 1, "prize": 700.0},
                {"min_rank": 2, "max_rank": 2, "prize": 450.0},
                {"min_rank": 3, "max_rank": 4, "prize": 100.0}
            ]
        },
        "questions": [
            {
                "game_type": "CROSSWORD",
                "difficulty": "HARD",
                "puzzle_data": {
                    "grid": [
                        ["F", "L", "U", "T", "T", "E", "R"],
                        ["X", "Y", "Z", "W", "A", "B", "C"]
                    ],
                    "row": 0,
                    "col": 0,
                    "direction": "horizontal"
                },
                "clues": "Google's UI toolkit for crafting beautiful, natively compiled applications.",
                "correct_answer": "FLUTTER",
                "points_reward": 200
            },
            {
                "game_type": "UNSCRAMBLE",
                "difficulty": "HARD",
                "puzzle_data": {"scrambled": "HPMISPGLORSAS"},
                "clues": "Modern UI design style utilizing frosted-glass effects.",
                "correct_answer": "GLASSMORPHISM",
                "points_reward": 150
            }
        ]
    }
]

def seed_games():
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        # 1. Seed Fruit Contests
        print("Seeding Fruit Slicing Contests...")
        fruit_count = 0
        for fc_data in FRUIT_CONTESTS:
            exists = db.query(FruitContest).filter(FruitContest.title == fc_data["title"]).first()
            if not exists:
                start = now + timedelta(hours=fc_data["offset_start_hours"])
                end = now + timedelta(hours=fc_data["offset_end_hours"])
                
                # Check status transitions
                status = "ACTIVE"
                if start > now:
                    status = "UPCOMING"
                elif end < now:
                    status = "COMPLETED"

                fc = FruitContest(
                    title=fc_data["title"],
                    entry_fee=fc_data["entry_fee"],
                    total_slots=fc_data["total_slots"],
                    joined_slots=random.randint(0, fc_data["total_slots"] - 5) if status != "UPCOMING" else 0,
                    prize_pool=fc_data["prize_pool"],
                    status=status,
                    prize_rules=json.dumps(fc_data["prize_rules"]),
                    seed=fc_data["seed"],
                    duration_seconds=fc_data["duration_seconds"],
                    start_time=start,
                    end_time=end,
                    created_at=now
                )
                db.add(fc)
                fruit_count += 1
        
        # 2. Seed Image Puzzle Contests
        print("Seeding Image Puzzle Contests...")
        puzzle_count = 0
        for pc_data in PUZZLE_CONTESTS:
            exists = db.query(ImagePuzzleContest).filter(ImagePuzzleContest.title == pc_data["title"]).first()
            if not exists:
                start = now + timedelta(hours=pc_data["offset_start_hours"])
                end = now + timedelta(hours=pc_data["offset_end_hours"])
                
                status = "ACTIVE"
                if start > now:
                    status = "UPCOMING"
                elif end < now:
                    status = "COMPLETED"

                pc = ImagePuzzleContest(
                    title=pc_data["title"],
                    entry_fee=pc_data["entry_fee"],
                    total_slots=pc_data["total_slots"],
                    joined_slots=random.randint(0, pc_data["total_slots"] - 5) if status != "UPCOMING" else 0,
                    prize_pool=pc_data["prize_pool"],
                    status=status,
                    prize_rules=json.dumps(pc_data["prize_rules"]),
                    image_url=pc_data["image_url"],
                    grid_size=pc_data["grid_size"],
                    duration_seconds=pc_data["duration_seconds"],
                    start_time=start,
                    end_time=end,
                    created_at=now
                )
                db.add(pc)
                puzzle_count += 1

        # 3. Seed Word Contests and Questions
        print("Seeding Word Guessing Contests & Questions...")
        word_contest_count = 0
        word_question_count = 0
        for wc_entry in WORD_CONTESTS_DATA:
            wc_data = wc_entry["contest"]
            exists = db.query(WordContest).filter(WordContest.title == wc_data["title"]).first()
            if not exists:
                start = now + timedelta(hours=wc_data["offset_start_hours"])
                end = now + timedelta(hours=wc_data["offset_end_hours"])
                
                status = "ACTIVE"
                if start > now:
                    status = "UPCOMING"
                elif end < now:
                    status = "COMPLETED"

                wc = WordContest(
                    title=wc_data["title"],
                    entry_fee=wc_data["entry_fee"],
                    total_slots=wc_data["total_slots"],
                    joined_slots=random.randint(0, wc_data["total_slots"] - 5) if status != "UPCOMING" else 0,
                    prize_pool=wc_data["prize_pool"],
                    difficulty=wc_data["difficulty"],
                    status=status,
                    prize_rules=json.dumps(wc_data["prize_rules"]),
                    duration_seconds=wc_data["duration_seconds"],
                    start_time=start,
                    end_time=end,
                    created_at=now
                )
                db.add(wc)
                db.flush()  # Generate wc.id for questions FK
                word_contest_count += 1

                # Seed questions for this contest
                for q_data in wc_entry["questions"]:
                    p_data_str = json.dumps(q_data["puzzle_data"]) if isinstance(q_data["puzzle_data"], (dict, list)) else str(q_data["puzzle_data"])
                    clues_str = json.dumps(q_data["clues"]) if isinstance(q_data["clues"], (dict, list)) else str(q_data["clues"])
                    
                    wq = WordQuestion(
                        contest_id=wc.id,
                        game_type=q_data["game_type"],
                        difficulty=q_data["difficulty"],
                        puzzle_data=p_data_str,
                        clues=clues_str,
                        correct_answer=q_data["correct_answer"],
                        points_reward=q_data["points_reward"],
                        created_at=now
                    )
                    db.add(wq)
                    word_question_count += 1

        db.commit()
        print(f"\nSeeding Complete!")
        print(f"- Seeded {fruit_count} new Fruit contests.")
        print(f"- Seeded {puzzle_count} new Slide Puzzle contests.")
        print(f"- Seeded {word_contest_count} new Word contests with {word_question_count} total questions.")

    except Exception as e:
        print(f"An error occurred during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_games()
