# admin_engine.py
# ----------------
# Admin, Monetization & Control Layer
# (Production-Grade Astrology App)

from datetime import datetime

# --------------------------------------------------
# USER TIERS
# --------------------------------------------------

TIERS = {
    "FREE": {
        "pdf": False,
        "questions": 0
    },
    "PREMIUM": {
        "pdf": True,
        "questions": 3
    },
    "VIP": {
        "pdf": True,
        "questions": 10
    }
}

# --------------------------------------------------
# IN-MEMORY ADMIN STORE
# (Replace with DB later)
# --------------------------------------------------

ADMIN_LOG = {}
USER_USAGE = {}

# --------------------------------------------------
# USER REGISTRATION
# --------------------------------------------------

def register_user(user_id, tier="FREE"):
    ADMIN_LOG[user_id] = {
        "tier": tier,
        "joined": datetime.now().isoformat(),
        "reports_generated": 0
    }

    USER_USAGE[user_id] = {
        "questions_left": TIERS[tier]["questions"]
    }


# --------------------------------------------------
# REPORT TRACKING
# --------------------------------------------------

def log_report_generation(user_id):
    if user_id not in ADMIN_LOG:
        register_user(user_id)

    ADMIN_LOG[user_id]["reports_generated"] += 1


# --------------------------------------------------
# Q&A CREDIT SYSTEM
# --------------------------------------------------

def can_ask_question(user_id):
    return USER_USAGE.get(user_id, {}).get("questions_left", 0) > 0


def deduct_question(user_id):
    if can_ask_question(user_id):
        USER_USAGE[user_id]["questions_left"] -= 1
        return True
    return False


def get_remaining_questions(user_id):
    return USER_USAGE.get(user_id, {}).get("questions_left", 0)


# --------------------------------------------------
# TIER UPGRADE (MANUAL / PAYMENT HOOK)
# --------------------------------------------------

def upgrade_user(user_id, new_tier):
    ADMIN_LOG[user_id]["tier"] = new_tier
    USER_USAGE[user_id]["questions_left"] = TIERS[new_tier]["questions"]


# --------------------------------------------------
# ADMIN DASHBOARD DATA
# --------------------------------------------------

def get_admin_summary():
    return {
        "total_users": len(ADMIN_LOG),
        "total_reports": sum(
            u["reports_generated"] for u in ADMIN_LOG.values()
        ),
        "tier_breakdown": {
            tier: len([u for u in ADMIN_LOG.values() if u["tier"] == tier])
            for tier in TIERS
        }
    }
