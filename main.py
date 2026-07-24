from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import time
import yt_dlp

player_last_seen = 0

app = FastAPI()

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://video-sender-website-renday.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# SQLite Database Setup
# -----------------------------

connection = sqlite3.connect(
    "queue.db",
    check_same_thread=False
)

cursor = connection.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    status TEXT NOT NULL
)
""")

connection.commit()

# -----------------------------
# Add Video
# -----------------------------

@app.post("/queue")
def add_video(video: dict):

    name = video.get("name", "Anonymous")

    if not name.strip():
        name = "Anonymous"

    cursor.execute(
        """
        INSERT INTO queue (name, url, status)
        VALUES (?, ?, ?)
        """,
        (
            name,
            video["url"],
            "queued"
        )
    )

    connection.commit()

    return {
        "message": "Video added"
    }

@app.post("/status/{video_id}")
def update_status(video_id: int, data: dict):

    cursor.execute(
        """
        UPDATE queue
        SET status = ?
        WHERE id = ?
        """,
        (
            data["status"],
            video_id
        )
    )

    connection.commit()

    return {
        "message": "Status updated"
    }


@app.post("/heartbeat")
def heartbeat():
    global player_last_seen

    player_last_seen = time.time()

    return {
        "status": "ok"
    }

@app.get("/player-status")
def player_status():

    if time.time() - player_last_seen < 15:
        return {
            "online": True
        }

    return {
        "online": False
    }

# -----------------------------
# Get Entire Queue
# -----------------------------

@app.get("/queue")
def get_queue():

    cursor.execute(
        """
        SELECT id, name, url, status
        FROM queue
        ORDER BY id ASC
        """
    )

    videos = cursor.fetchall()

    result = []

    for video in videos:
        result.append({
            "id": video[0],
            "name": video[1],
            "url": video[2],
            "status": video[3]
        })

    return result


# -----------------------------
# Get Next Video
# -----------------------------

@app.get("/next")
def get_next_video():

    cursor.execute(
        """
        SELECT id, name, url, status
        FROM queue
        ORDER BY id ASC
        LIMIT 1
        """
    )

    video = cursor.fetchone()

    if video is None:
        return {
            "message": "Queue empty"
        }

    return {
        "id": video[0],
        "name": video[1],
        "url": video[2]
    }


# -----------------------------
# Remove Finished Video
# -----------------------------

@app.post("/finished")
def finished_video():

    cursor.execute(
        """
        SELECT id
        FROM queue
        ORDER BY id ASC
        LIMIT 1
        """
    )

    video = cursor.fetchone()

    if video is None:
        return {
            "message": "Queue empty"
        }

    time.sleep(30)
    cursor.execute(
        """
        DELETE FROM queue
        WHERE id = ?
        """,
        (video[0],)
    )

    connection.commit()


    return {
        "message": "Video removed"
    }


# -----------------------------
# Delete Specific Video
# -----------------------------

@app.delete("/queue/{video_id}")
def delete_video(video_id: int):

    cursor.execute(
        """
        DELETE FROM queue
        WHERE id = ?
        """,
        (video_id,)
    )

    connection.commit()

    return {
        "message": "Video deleted"
    }


# -----------------------------
# Test Route
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "Video Queue API running"
    }