models.py:
    - contains 7 SQLAlchemy models
        - User
        - Tag
        - Song
        - ListeningEvent
        - Rating
        - Playlist
        - Notification
    - 3 join tables
        - friendships (many-to-many, symmetric)
        - song_tags (many-to-many)
        - playlist_entries (many-to-many w/ ordering)

routes/:

4 thin blueprints, one per domain. Each parses the request, calls a service, and formats the JSON response.

    - songs.py
        handles searching, viewing, rating and listening
        pulls from search_service, notification_service, streak_service
    - playlist.py
        creates a playlist, returns playlist metadata, returns ordered list of songs in playlist, adds a song to the playlist
    - users.py
        returns a user's profile, current listening streak, notifications, and marks a notification as read
    - feed.py
        gets a friends' single most recent song each, or a broader stream of recent friend activities

services/:

Business logic.

    - feed_service.py (2 functions)
        - get_friends_listening_now
            return each friend's single most recent song within last 24 hours, newest one first.
        - get_activity_feed:
            broader activity log. Returns most recent 'limit' events from friends regardless of time

    - streak_service.py (3 functions)
        - record_listening_event(user_id, song_id)
            creates ListeningEvent, calls streak update
        - update_listening_streak(user, now)
            updates the streak IN PLACE dependent on user's listening history
        - get_streak(user_id)
            returns streak

    - search_service.py (2 functions)
        - search_songs(query)
            case-insensitive search on title or artist, returns matching song dicts
        - get_song(song_id)
            fetch one song by id

    - playlist_service.py (2 functions)
        - create_playlist(name, created_by_user_id, iscollaborative=True)
            creates and commits a new Playlist, validating the user exists
        - get_playlist_songs(playlist_id)
            returns the playlist's song ordered by position. Responsible for returning ALL songs in playlist order.
        - get_playlist(playlist_id)
        - get_user_palylists(user_id)

    - notification_service.py (3 functions)
        - create_notification(user_id, notification_type, body)
            creates + commits Notification
        - add_to_playlist(playlist_id, song_id, added_by_user_id)
            adds a song to the playlist, notifying song's original sharer. Responsible for both playlist mutation and side-effect notifications.
        - rate_song(user_id, song_id, score)
            validates score 1-5, then creates a new Rating or updates user's existing one
        - get_notifications(user_id, unread_only=False)
        - mark_as_read(notification_id)


Data flow trace:

Scenario 1: A friend listens to a song.
When a friend listens to a song, here's what happens.
1. POST /songs/<song_id>/listen occurs, which gets the user_id of the friend that's listening to the song.
2. Once POST occurs, it calls record_listening_event(user_id, song_id), which loads the user and creates a listening event with user_id, song_id, and listened_at alongside a db.session.add(...). 
3. Updates the listening_streak of the user listening to the song.
4. Commits to the db session.

On the other side (the users' side, not the friend):
1. "GET /feed/<user_id>/listening-now" calls listening_now, which calls get_friends_listening_now(user_id)
2. Loads the user's info, gets friends_id from user.friends.
3. Calls ListeningEvent with user_id in friends_id and their listened_at is >= now - 24hr.
4. Recalibrates the list to show the most recent song for your friends
5. Returns the list with the newly updated friend's list and their song

Scenario 2: User rates a song
1. POST /songs/<id>/rate with {user_id, score}
2. sent to songs.py, rate()
3. notification_services.rate_songs() validates 1 <= score <= 5
4. updates the Rating row

Scenario 3: User adds a song to a playlist
1. POST /playlists/<id>/songs with {song_id, added_by}
2. Sent to playlist.py: add_song() --> notification_service.add_to_playlist(), adding song to the playlist.songs.


Tackling:

Issue #1
Issue #3
Issue #4