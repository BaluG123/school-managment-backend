# SAttendance API

Django REST API backend for **Student Attendance Management** — built for schools moving from manual registers to digital face-based attendance via a React Native mobile app.

## Features

- **Authentication** — JWT-based signup/login for headmasters and school staff
- **School Management** — Create and manage school details
- **Classroom Management** — Organize students by grade, section, and academic year
- **Student Registration** — Store student info + reference face photo for recognition
- **Attendance Marking** — Mark daily attendance with timestamp, face confidence score, and capture photo
- **Reports** — Class-wise, student-wise, and school-wide daily dashboards
- **Swagger Docs** — Interactive API documentation at `/api/docs/`

## Quick Start

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional: customize settings
python manage.py migrate
python manage.py createsuperuser  # optional: for Django admin
python manage.py runserver
```

Server runs at: **http://127.0.0.1:8000**

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- Health check: http://127.0.0.1:8000/api/health/

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup/` | Register headmaster/staff account |
| POST | `/api/auth/login/` | Login (returns JWT tokens) |
| POST | `/api/auth/refresh/` | Refresh access token |
| GET | `/api/auth/profile/` | Get current user profile |
| POST | `/api/auth/change-password/` | Change password |

### Schools
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/schools/` | List / create school |
| GET/PUT/PATCH | `/api/schools/{id}/` | View / update school |

### Classrooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/schools/classrooms/` | List / create classroom |
| GET/PUT/PATCH/DELETE | `/api/schools/classrooms/{id}/` | Manage classroom |

### Students
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/students/` | List / register student (multipart for face photo) |
| GET/PUT/PATCH/DELETE | `/api/students/{id}/` | View / edit / deactivate student |
| PATCH | `/api/students/{id}/face-photo/` | Update face photo only |
| GET | `/api/students/face-photos/?classroom={id}` | Get all face photos for a class (mobile matching) |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/attendance/mark/` | Mark attendance (after face match on mobile) |
| POST | `/api/attendance/bulk-mark/` | Manual bulk attendance |
| GET | `/api/attendance/` | List records (filter by date, class, student) |
| GET | `/api/attendance/class-report/?classroom={id}&date=` | Class-wise report |
| GET | `/api/attendance/student-report/?student={id}&from=&to=` | Student-wise history |
| GET | `/api/attendance/dashboard/?date=` | School-wide daily dashboard |

## React Native Integration Flow

1. **Signup/Login** → store JWT access + refresh tokens
2. **Create School** → links school to logged-in user
3. **Add Classrooms** → e.g. Class 10-A, 2025-2026
4. **Register Students** → upload face photo with student details
5. **Daily Attendance:**
   - `GET /api/students/face-photos/?classroom=1` → download reference photos
   - Run face recognition + liveness on device
   - `POST /api/attendance/mark/` with `student_id`, `face_match_confidence`, `capture_photo`
6. **View Reports** → class-report, student-report, dashboard endpoints

## Auth Header

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

## Example: Signup

```json
POST /api/auth/signup/
{
  "username": "headmaster_school1",
  "password": "securepass123",
  "password_confirm": "securepass123",
  "email": "head@school.com",
  "phone": "9876543210",
  "role": "headmaster"
}
```

## Example: Mark Attendance (multipart)

```
POST /api/attendance/mark/
Content-Type: multipart/form-data

student_id: 5
status: present
face_match_confidence: 94.5
capture_photo: <image file>
```

## Project Structure

```
backend/
├── accounts/       # Auth, signup, JWT, headmaster profiles
├── schools/        # School & classroom models
├── students/       # Student registration & face photos
├── attendance/     # Attendance marking & reports
├── core/           # Shared validators & permissions
├── config/         # Django settings & URLs
├── media/          # Uploaded images (face photos, captures)
└── manage.py
```

## Production Notes

- Set `DEBUG=False` and a strong `SECRET_KEY` in `.env`
- Use PostgreSQL instead of SQLite
- Configure proper `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`
- Serve media files via nginx/S3
- Add `django-storages` for cloud image storage
