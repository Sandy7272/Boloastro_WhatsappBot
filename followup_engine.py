# followup_engine.py
# ------------------
# Auto Follow-up Scheduler (WhatsApp)

from datetime import datetime, timedelta

FOLLOWUPS = [
    {
        "delay_hours": 1,
        "text": (
            "📘 Have you read your Kundali?\n\n"
            "You can ask questions like:\n"
            "• When will I get married?\n"
            "• Best year for career growth?"
        )
    },
    {
        "delay_hours": 24,
        "text": (
            "🔮 Tip:\n\n"
            "Marriage and career timing depends on Dasha & planetary strength.\n"
            "You can still ask your questions."
        )
    },
    {
        "delay_hours": 72,
        "text": (
            "✨ Upgrade Reminder ✨\n\n"
            "VIP users get:\n"
            "• More questions\n"
            "• Priority predictions\n"
            "• Future transit analysis"
        )
    }
]

def schedule_followups(session):
    now = datetime.now()
    session["followups"] = [
        {
            "time": now + timedelta(hours=f["delay_hours"]),
            "text": f["text"],
            "sent": False
        }
        for f in FOLLOWUPS
    ]
