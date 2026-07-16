from app import create_app, db
from models import User, Song, Notification
from services.notification_service import rate_song, get_notifications

app = create_app()

with app.app_context():
    song = db.session.query(Song).filter(Song.shared_by.isnot(None)).first()
    sharer_id = song.shared_by
    rater = db.session.query(User).filter(User.id != sharer_id).first()

    sharer_before = len(get_notifications(sharer_id))
    total_before = db.session.query(Notification).count()

    rating = rate_song(rater.id, song.id, 5)

    sharer_after = len(get_notifications(sharer_id))
    total_after = db.session.query(Notification).count()
    print(f"rating saved with score {rating.score}")
    print(f"sharer notifications: {sharer_before} -> {sharer_after}")
    print(f"total notifications:  {total_before} -> {total_after}")
    if total_after == total_before:
        print("BUG CONFIRMED: rating created no notification.")
