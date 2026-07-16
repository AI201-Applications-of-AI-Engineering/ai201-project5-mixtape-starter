from typing import Any


from app import create_app, db
from models import Song, song_tags

app = create_app()

with app.app_context():
    raw_rows = (
        db.session.query(Song.id)
        .outerjoin(song_tags, Song.id == song_tags.c.song_id)
        .filter(Song.title.ilike("%Anthem%"))
        .all()
    )
    print(f"Raw rows the search query produces for 'Anthem': {len(raw_rows)}")

    distinct_songs = db.session.query(Song).filter(Song.title.ilike("%Anthem%")).count()
    print(f"Actual distinct songs matching 'Anthem': {distinct_songs}")
