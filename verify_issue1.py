from datetime import datetime, timedelta, timezone
from models import User
from services.streak_service import update_listening_streak

# 2026-07-13 is a Monday, so this 7-day window covers Mon..Sun.
base = datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc)

print(f"{'today (weekday)':<30}{'before':>8}{'after':>8}")
print("-" * 46)
for offset in range(7):
    today = base + timedelta(days=offset)

    # A user who listened YESTERDAY, on a 12-day streak.
    # This is a normal consecutive-day listen -> should always give 13.
    user = User(username="kenji", email="k@x.app")
    user.listening_streak = 12
    user.last_listened_at = today - timedelta(days=1)

    update_listening_streak(user, today)

    flag = "  <-- streak reset!" if user.listening_streak == 1 else ""
    label = f"{today.date()} ({today.strftime('%A')}):"
    print(f"{label:<30}{12:>8}{user.listening_streak:>8}{flag}")