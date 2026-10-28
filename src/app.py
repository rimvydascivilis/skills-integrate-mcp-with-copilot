"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Cookie, Depends, FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")
teachers_file = current_dir / "teachers.json"
sessions = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def load_teachers():
    try:
        with teachers_file.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to load teacher credentials: {error}") from error

    teachers = data.get("teachers")
    if not isinstance(teachers, list):
        raise RuntimeError("Teacher credentials must contain a 'teachers' list")
    return teachers


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120_000
    ).hex()


def authenticate_teacher(username, password):
    for teacher in load_teachers():
        if teacher.get("username") != username:
            continue
        salt = teacher.get("salt")
        password_hash = teacher.get("password_hash")
        if not salt or not password_hash:
            continue
        if hmac.compare_digest(hash_password(password, salt), password_hash):
            return username
    return None


def require_teacher(session: str | None = Cookie(default=None, alias="teacher_session")):
    username = sessions.get(session)
    if not username:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/auth/login")
def login(credentials: LoginRequest):
    username = authenticate_teacher(credentials.username, credentials.password)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    session = secrets.token_urlsafe(32)
    sessions[session] = username
    response = JSONResponse({"username": username})
    response.set_cookie(
        "teacher_session",
        session,
        httponly=True,
        samesite="lax",
        max_age=8 * 60 * 60,
    )
    return response


@app.get("/auth/me")
def current_teacher(
    username: str = Depends(require_teacher),
):
    return {"username": username}


@app.post("/auth/logout")
def logout(
    session: str | None = Cookie(default=None, alias="teacher_session"),
):
    if session:
        sessions.pop(session, None)
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie("teacher_session")
    return response


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    _teacher: str = Depends(require_teacher),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
