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

Issue #1: My listening streak keeps resetting
Reported by: kenji

I listen to something on Mixtape every single day — I haven't missed a day in weeks. On Saturday night my streak was at 12. Sunday morning I played a song like always, checked my profile, and my streak said 1. This is the second time it's happened, and both times it was a Sunday. Listening again on Monday bumped it to 2, so it's counting again — it just threw away my whole streak.

Steps I took:

Listened to a song every calendar day, including Saturday.
Listened again Sunday morning and checked my streak (GET /users/<my_id>/streak).
Expected: streak goes from 12 to 13 — I listened on consecutive days. Actual: streak shows 1, as if I'd skipped a day.

Issue #3: The same song keeps showing up twice in search
Reported by: simone

When I search, some songs come back two or even three times — identical entries, same song. I searched "Anthem" and Crown Heights Anthem by Borough Kings showed up three times in the results. Other songs only show up once. Nothing about the duplicates looks different; it's just the same result repeated.

Steps I took:

Searched for a song (GET /songs/search?q=Anthem).
Counted the results.
Expected: each matching song appears exactly once. Actual: some songs appear once, others two or three times, for a single-song match.

Issue #4: I got notified when a friend added my song to a playlist but not when they rated it

Reported by: aaliya

Notifications work when someone adds a song I shared to a playlist — I get "kenji added your song…" right away. But when kenji rated one of my songs (he showed me, 5 stars), I never got a notification. No delay, just nothing, and there's nothing in my notification list (GET /users/<my_id>/notifications) either. Ratings notifications seem to just not happen, for anyone I've asked.

Steps I took:

Had a friend add my shared song to a playlist → notification arrived. ✅
Had the same friend rate a different song I shared (POST /songs/<song_id>/rate) → checked my notifications.
Expected: a notification for the rating, same as for the playlist add. Actual: rating is saved (it shows on the song), but no notification is ever created.

# Issue 1

## How I reproduced it

In order to verify that the bug existed, I asked Claude to help build a Python script that will get what I needed. Specifically, because we know that Sunday is when the bug occurs, I had the script incorporate all 7 days of the week, and utilize the function listening_streak to grab the streak. Using the current day as the input, and a sample user, I was able to reproduce the bug, and found, like the user said, only Sunday reseted the streak to 1.

# Issue 3

## How I reproduced it
To see the 3 rows when searching a song, I asked Claude to help me with generating a Python script that can test what simone experienced. Using "Anthem" as the query, I checked the database to see how many rows it returned for the name, and it returned 3, while the actual number of songs remained 1.

# Issue 4

## How I reproduced it
Like before, I asked Claude to help me replicate the environment in which the bug occurred with the user. Using a sample rater, we tested a before and after rating, where we got the notification count before the rating, and the notification count after the rating. Because it remained the same, we were able to find the bug was actually there.