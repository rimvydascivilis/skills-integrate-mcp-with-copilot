# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities as an authenticated teacher
- Unregister students as an authenticated teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

3. **Teachers** - Stored in `src/teachers.json`:
   - Username
   - PBKDF2 password hash
   - Unique salt

To add a teacher, generate a salt and password hash with:

```bash
python -c "import hashlib, secrets; p='replace-with-password'; s=secrets.token_hex(16); print({'username': 'teacher', 'salt': s, 'password_hash': hashlib.pbkdf2_hmac('sha256', p.encode(), s.encode(), 120000).hex()})"
```

Add the resulting object to the `teachers` array in `src/teachers.json`. Activity browsing remains public, but signup and unregister requests require a teacher login.

All data is stored in memory, which means data will be reset when the server restarts.
