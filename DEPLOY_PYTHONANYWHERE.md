# PythonAnywhere Deployment Guide — SAttendance Backend

Deploy to: `https://YOUR_USERNAME.pythonanywhere.com`

Replace `YOUR_USERNAME` with your PythonAnywhere username (e.g. `balug123`).

---

## Part 1 — Deploy Backend to PythonAnywhere

### Step 1: Open PythonAnywhere Dashboard

1. Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com) and log in
2. Note your username (top-right) — your API URL will be:
   ```
   https://YOUR_USERNAME.pythonanywhere.com/api
   ```

---

### Step 2: Open a Bash Console

1. Click **Consoles** → **Bash**
2. Run these commands (replace `YOUR_USERNAME`):

```bash
cd ~
git clone https://github.com/BaluG123/school-managment-backend.git
cd school-managment-backend
```

---

### Step 3: Create Virtual Environment & Install Dependencies

```bash
mkvirtualenv --python=/usr/bin/python3.10 sattendance-env
# If mkvirtualenv fails, use:
# python3.10 -m venv venv && source venv/bin/activate

pip install -r requirements.txt
```

---

### Step 4: Create `.env` File

```bash
nano .env
```

Paste this (edit values):

```env
SECRET_KEY=put-a-long-random-string-here-at-least-50-chars
DEBUG=False
ALLOWED_HOSTS=YOUR_USERNAME.pythonanywhere.com
```

Generate a secret key locally:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Save: `Ctrl+O`, Enter, `Ctrl+X`

---

### Step 5: Run Migrations & Collect Static Files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
mkdir -p media
```

Optional — create admin user:
```bash
python manage.py createsuperuser
```

---

### Step 6: Configure the Web App

1. Go to **Web** tab → **Add a new web app**
2. Choose **Manual configuration** (NOT Django wizard)
3. Select **Python 3.10**

#### 6a. Set Virtualenv

In the Web tab, set **Virtualenv** to:
```
/home/YOUR_USERNAME/school-managment-backend/venv
```
(or `/home/YOUR_USERNAME/.virtualenvs/sattendance-env` if you used mkvirtualenv)

#### 6b. Edit WSGI File

Click the **WSGI configuration file** link and replace ALL content with:

```python
import os
import sys

path = '/home/YOUR_USERNAME/school-managment-backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Save the file.

#### 6c. Map Static Files

In the Web tab, under **Static files**, add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/YOUR_USERNAME/school-managment-backend/staticfiles` |

#### 6d. Map Media Files (face photos)

Add another static files mapping:

| URL | Directory |
|-----|-----------|
| `/media/` | `/home/YOUR_USERNAME/school-managment-backend/media` |

> This is required so student face photos are accessible from the mobile app.

---

### Step 7: Reload the Web App

Click the green **Reload** button on the Web tab.

---

### Step 8: Verify HTTPS API

Open in browser:

| URL | Expected |
|-----|----------|
| `https://YOUR_USERNAME.pythonanywhere.com/api/health/` | `{"status":"ok",...}` |
| `https://YOUR_USERNAME.pythonanywhere.com/api/docs/` | Swagger UI |

Test signup:
```bash
curl -X POST https://YOUR_USERNAME.pythonanywhere.com/api/auth/signup/ \
  -H "Content-Type: application/json" \
  -d '{"username":"headmaster1","password":"securepass123","password_confirm":"securepass123","email":"head@school.com","phone":"9876543210","role":"headmaster"}'
```

---

## Part 2 — Connect Mobile App to Production

### Step 9: Update API URL in the App

Edit `headmaster/src/constants/config.ts`:

```typescript
const PRODUCTION_API = 'https://YOUR_USERNAME.pythonanywhere.com/api';
const USE_PRODUCTION = true;   // ← flip this to true
```

---

### Step 10: Build APK for Real Device

On your Mac, in the `headmaster` folder:

```bash
cd headmaster

# Make sure Metro is NOT needed for release build
cd android
./gradlew assembleDebug
```

APK location:
```
headmaster/android/app/build/outputs/apk/debug/app-debug.apk
```

---

### Step 11: Install APK on Your Phone

**Option A — USB (ADB):**
```bash
# Enable Developer Options + USB Debugging on phone
adb install android/app/build/outputs/apk/debug/app-debug.apk
```

**Option B — Share APK file:**
- Copy `app-debug.apk` to Google Drive / WhatsApp
- Open on phone → Install (allow "Install from unknown sources")

---

### Step 12: Test on Real Device

1. Phone must have **internet** (WiFi or mobile data)
2. Open **SAttendance** app
3. **Sign Up** → create headmaster account
4. **Create School** → add school details
5. **Add Classroom** → from dashboard
6. **Register Student** → with face photo
7. **Mark Attendance** → face scan test

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `DisallowedHost` error | Add `YOUR_USERNAME.pythonanywhere.com` to `.env` ALLOWED_HOSTS |
| `502 Bad Gateway` | Check WSGI file path and virtualenv path |
| Signup fails on phone | Confirm `USE_PRODUCTION = true` and URL is `https://` |
| Face photos not loading | Check `/media/` static files mapping in Web tab |
| App can't connect | Test `https://YOUR_USERNAME.pythonanywhere.com/api/health/` in phone browser |
| Build fails | Run `cd android && ./gradlew clean assembleDebug` |

---

## Updating Backend After Code Changes

On PythonAnywhere Bash console:

```bash
cd ~/school-managment-backend
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

Then **Reload** the web app from the Web tab.

---

## Your URLs (fill in after deploy)

- API Base: `https://YOUR_USERNAME.pythonanywhere.com/api`
- Swagger: `https://YOUR_USERNAME.pythonanywhere.com/api/docs/`
- Admin: `https://YOUR_USERNAME.pythonanywhere.com/admin/`
- Health: `https://YOUR_USERNAME.pythonanywhere.com/api/health/`
