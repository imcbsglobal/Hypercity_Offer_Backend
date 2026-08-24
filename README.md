# Hypercity Offer App - Backend

## Overview
Django REST backend for Hypercity supermarket offer management. Provides admin panel (Django Admin) for management and REST APIs for the mobile app.

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Framework | Django 6.0 + Django REST Framework |
| Auth | JWT (cust OTP) + Django Admin (staff) |
| Database | SQLite (dev), upgradeable to PostgreSQL |
| Task Queue | Celery + Redis (async push, offer expiry) |
| Push | Firebase Cloud Messaging |
| Docs | Swagger (drf-spectacular) |

## Project Structure
```
backend/
├── config/                 # Django project settings, urls, wsgi, celery
│   ├── settings.py
│   ├── urls.py             # Root URL routing
│   ├── celery.py           # Celery app config
│   └── __init__.py
├── apps/
│   ├── accounts/           # User model, OTP auth, JWT, role permissions
│   ├── branches/           # Branch CRUD
│   ├── offers/             # Offer CRUD with branch assignment
│   ├── banners/            # Banner CRUD with scheduling
│   └── notifications/      # FCM push + user notification history
├── media/                  # Uploaded images (offers, banners, branches)
├── manage.py
├── .env                    # Environment configuration
├── requirements.txt
└── README.md
```

## Roles & Permissions

| Capability | Super Admin | Branch Manager | Marketing Manager |
|------------|:-----------:|:--------------:|:-----------------:|
| Manage Users | ✅ | ❌ | ❌ |
| Manage all Branches | ✅ | ❌ | ❌ |
| View own Branch | ✅ | ✅ | ❌ |
| Create/Edit Offers | ✅ | ❌ | ✅ |
| Send Notifications | ✅ | ❌ | ✅ |
| Manage Banners | ✅ | ❌ | ✅ |
| View Dashboard | ✅ | Own branch | ✅ |

## Models

### User
- `phone` (unique, login field), `name`, `role` (SUPER_ADMIN/BRANCH_MGR/MARKETING)
- `managed_branch` (FK → Branch, for Branch Managers)
- `fcm_token` (for push notifications), `preferred_branches` (M2M)
- `is_customer` (for mobile app users)

### Branch
- `name`, `address`, `phone`, `image`, `is_active`

### Offer
- `title`, `description`, `image`
- `start_date`, `end_date`, `terms_conditions`
- `branches` (M2M through OfferBranch), `view_count`, `is_active`

### Banner
- `title`, `image`, `link_url`, `linked_offer` (FK → Offer)
- `branches` (M2M, optional targeting), `start_date`, `end_date`
- `order` (sorting), `is_active`

### Notification
- `title`, `body`, `image`, `type` (COMMON/OFFER/PROMO)
- `linked_offer` (FK → Offer), `target_branches` (M2M)
- `is_active`, `sent_at`, `created_by`

### UserNotification (join table)
- Tracks which user received which notification
- `is_read`, `read_at`

## API Endpoints

### Auth
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/send-otp/` | Public | Send OTP to phone |
| POST | `/api/auth/verify-otp/` | Public | Login existing user with OTP |
| POST | `/api/auth/signup/` | Public | Signup new user with OTP + name |
| POST | `/api/auth/admin-login/` | Public | Admin login with phone + password |
| POST | `/api/auth/refresh/` | Public | Refresh JWT token |
| GET/PUT | `/api/profile/` | JWT | Get/update user profile |

### Branches
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/branches/` | Public | List active branches |
| GET | `/api/branches/{id}/` | Public | Branch detail |
| POST | `/api/branches/` | JWT+SuperAdmin | Create branch |
| PUT/DELETE | `/api/branches/{id}/` | JWT+SuperAdmin | Update/delete branch |

### Offers
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/offers/` | Public | Active offers (filter: `?branch=X`, `?expiring_soon=true`) |
| GET | `/api/offers/{id}/` | Public | Offer detail (increments view_count) |
| POST | `/api/offers/` | JWT+Marketing | Create offer |
| PUT/DELETE | `/api/offers/{id}/` | JWT+Marketing | Update/delete offer |
| GET | `/api/offers/admin_all/` | JWT | All offers (incl. inactive) |

### Banners
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/banners/` | Public | Active banners |
| POST | `/api/banners/` | JWT+Marketing | Create banner |
| PUT/DELETE | `/api/banners/{id}/` | JWT+Marketing | Update/delete banner |

### Notifications
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/api/notifications/` | JWT | List/create notifications |
| GET | `/api/notifications/my/` | JWT | My notifications |
| POST | `/api/notifications/mark_read/` | JWT | Mark notification as read |
| GET | `/api/notifications/unread_count/` | JWT | Unread notification count |

### Admin
| Endpoint | Description |
|----------|-------------|
| `/admin/` | Django Admin panel |
| `/api/docs/` | Swagger API documentation |

## Setup & Run

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser --phone=9999999999 --name="Admin"
python manage.py runserver
```

## Environment Variables (.env)
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
FIREBASE_CREDENTIALS_PATH=
CELERY_BROKER_URL=redis://localhost:6379/0
```

## Celery (for async tasks)
```bash
# Start Celery worker (terminal 1)
celery -A config worker -l info

# Start Celery beat for scheduled tasks (terminal 2)
celery -A config beat -l info
```

## Admin Workflow

### Super Admin
```
/admin/ login → Manage Users/Branches/Offers/Banners/Notifications

```

### Branch Manager
```

/admin/ login → View only their branch offers and data

```

### Marketing Manager
```
/admin/ login → Create offers, banners, and send push notifications
```
