# API Details — Hypercity Offer App

## Base URL
```
http://127.0.0.1:8000/api/
```

## Authentication
- **Customer:** OTP flow (`send-otp` → `verify-otp` for login / `signup` for new users → JWT)
- **Admin:** `admin-login` (phone + password → JWT)
- **Header:** `Authorization: Bearer <access_token>`

---

## 1. Auth Endpoints

### 1.1 Send OTP
```
POST /api/auth/send-otp/
```
**Auth:** Public

**Request:**
```json
{
  "phone": "9876543210"
}
```

**Response 200:**
```json
{
  "message": "OTP sent successfully",
  "otp": "4574"
}
```

**Response 400:**
```json
{
  "phone": ["Invalid phone number"]
}
```

---

### 1.2 Verify OTP (Login)
```
POST /api/auth/verify-otp/
```
**Auth:** Public  
**Note:** For existing users only. New users should use `/api/auth/signup/`.

**Request:**
```json
{
  "phone": "9876543210",
  "otp": "4574"
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 4,
    "phone": "9876543210",
    "name": "User",
    "is_customer": true,
    "role": "SUPER_ADMIN"
  }
}
```

**Response 400:**
```json
{
  "error": "Invalid OTP"
}
```

```json
{
  "error": "OTP expired"
}
```

```json
{
  "error": "Account not found. Please signup first."
}
```

---

### 1.3 Signup
```
POST /api/auth/signup/
```
**Auth:** Public  
**Note:** For new users only. Existing users should use `/api/auth/verify-otp/` for login.

**Request:**
```json
{
  "phone": "9876543210",
  "otp": "4574",
  "name": "John Doe"
}
```

**Response 201:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 5,
    "phone": "9876543210",
    "name": "John Doe",
    "is_customer": true,
    "role": "CUSTOMER"
  }
}
```

**Response 400:**
```json
{
  "phone": ["Invalid phone number"]
}
```

```json
{
  "error": "Invalid OTP"
}
```

```json
{
  "error": "OTP expired"
}
```

```json
{
  "error": "Account already exists. Please login."
}
```

---

### 1.4 Admin Login
```
POST /api/auth/admin-login/
```
**Auth:** Public

**Request:**
```json
{
  "phone": "9999999999",
  "password": "admin123"
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "phone": "9999999999",
    "name": "Super Admin",
    "role": "SUPER_ADMIN",
    "managed_branch": null,
    "is_superuser": true
  }
}
```

**Response 401:**
```json
{
  "error": "Invalid credentials or not a staff user"
}
```

---

### 1.5 Refresh Token
```
POST /api/auth/refresh/
```
**Auth:** Public

**Request:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

## 2. Profile

### 2.1 Get Profile
```
GET /api/profile/
```
**Auth:** JWT

**Response 200:**
```json
{
  "id": 4,
  "phone": "6666666666",
  "name": "Customer 1",
  "email": "",
  "fcm_token": "",
  "preferred_branches": [],
  "role": "SUPER_ADMIN",
  "is_customer": true
}
```

---

### 2.2 Update Profile
```
PUT /api/profile/
```
**Auth:** JWT

**Request:**
```json
{
  "name": "Updated Name",
  "email": "user@example.com",
  "fcm_token": "dGhpcyBpcyBhIHRva2Vu...",
  "preferred_branches": [1, 2]
}
```

**Response 200:**
```json
{
  "id": 4,
  "phone": "6666666666",
  "name": "Updated Name",
  "email": "user@example.com",
  "fcm_token": "dGhpcyBpcyBhIHRva2Vu...",
  "preferred_branches": [1, 2],
  "role": "SUPER_ADMIN",
  "is_customer": true
}
```

---

## 3. Branches

### 3.1 List Branches
```
GET /api/branches/
```
**Auth:** Public

**Query Parameters:**
| Param | Type | Example | Description |
|-------|------|---------|-------------|
| search | string | `?search=Koramangala` | Search by name or address |
| ordering | string | `?ordering=name` | `name`, `-name`, `created_at` |
| page | int | `?page=2` | Page number |

**Response 200:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Hypercity - Koramangala",
      "address": "123, Main Road, Koramangala, Bangalore - 560034",
      "phone": "080-12345678",
      "image": null,
      "is_active": true
    },
    {
      "id": 2,
      "name": "Hypercity - Indiranagar",
      "address": "456, Double Road, Indiranagar, Bangalore - 560038",
      "phone": "080-87654321",
      "image": null,
      "is_active": true
    }
  ]
}
```

---

### 3.2 Get Branch Detail
```
GET /api/branches/{id}/
```
**Auth:** Public

**Response 200:**
```json
{
  "id": 1,
  "name": "Hypercity - Koramangala",
  "address": "123, Main Road, Koramangala, Bangalore - 560034",
  "phone": "080-12345678",
  "image": null,
  "is_active": true,
  "created_at": "2026-06-11T12:00:00+05:30",
  "updated_at": "2026-06-11T12:00:00+05:30"
}
```

---

### 3.3 Create Branch
```
POST /api/branches/
```
**Auth:** JWT (Super Admin / Branch Manager)

**Request (JSON):**
```json
{
  "name": "Hypercity - Whitefield",
  "address": "789, ITPL Main Road, Whitefield, Bangalore",
  "phone": "080-11223344",
  "is_active": true
}
```

**Request (multipart/form-data — with image):**
| Field | Type |
|-------|------|
| name | text |
| address | text |
| phone | text |
| image | file |
| is_active | checkbox |

**Response 201:** Full branch detail (same as GET detail).

---

### 3.4 Update Branch
```
PUT /api/branches/{id}/
```
**Auth:** JWT (Super Admin / Branch Manager)

**Request:** Same fields as create.

**Response 200:** Updated branch detail.

---

### 3.5 Delete Branch
```
DELETE /api/branches/{id}/
```
**Auth:** JWT (Super Admin / Branch Manager)

**Response 204:** No content.

---

## 4. Offers

### 4.1 List Offers
```
GET /api/offers/
```
**Auth:** Public

**Query Parameters:**
| Param | Type | Example | Description |
|-------|------|---------|-------------|
| branch | int | `?branch=1` | Filter by branch ID |
| expiring_soon | bool | `?expiring_soon=true` | Ending within 3 days |
| search | string | `?search=dairy` | Search title/description |
| ordering | string | `?ordering=-view_count` | Sort by field |
| page | int | `?page=1` | Page number |

**Response 200:**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "50% Off on All Dairy Products",
      "description": "Get flat 50% off on all dairy items",
      "image": "http://127.0.0.1:8000/media/offers/dairy.jpg",
      "start_date": "2026-06-10T00:00:00+05:30",
      "end_date": "2026-06-20T23:59:59+05:30",
      "is_active": true,
      "view_count": 0
    }
  ]
}
```

---

### 4.2 Get Offer Detail
```
GET /api/offers/{id}/
```
**Auth:** Public  
*(Increments view_count by 1)*

**Response 200:**
```json
{
  "id": 1,
  "title": "50% Off on All Dairy Products",
  "description": "Get flat 50% off on all dairy items",
  "image": "http://127.0.0.1:8000/media/offers/dairy.jpg",
  "start_date": "2026-06-10T00:00:00+05:30",
  "end_date": "2026-06-20T23:59:59+05:30",
  "terms_conditions": "Valid only on MRP items. Cannot be clubbed with other offers.",
  "is_active": true,
  "view_count": 5,
  "branches": [
    {
      "id": 1,
      "branch": 1,
      "branch_detail": {
        "id": 1,
        "name": "Hypercity - Koramangala",
        "address": "123, Main Road, Koramangala",
        "phone": "080-12345678",
        "image": null,
        "is_active": true
      },
      "is_active": true
    }
  ],
  "created_by_name": "Super Admin",
  "created_at": "2026-06-11T12:00:00+05:30",
  "updated_at": "2026-06-11T12:00:00+05:30"
}
```

---

### 4.3 Create Offer
```
POST /api/offers/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Request (JSON):**
```json
{
  "title": "50% Off on All Dairy Products",
  "description": "Get flat 50% off on all dairy items at Hypercity",
  "start_date": "2026-06-10T00:00:00+05:30",
  "end_date": "2026-06-20T23:59:59+05:30",
  "terms_conditions": "Valid only on MRP items.",
  "branch_ids": [1, 2]
}
```

**Request (multipart/form-data — with image):**
| Field | Type |
|-------|------|
| title | text |
| description | text |
| image | file |
| start_date | text |
| end_date | text |
| terms_conditions | text |
| branch_ids | text (comma-separated or JSON array) |

**Response 201:** Full offer detail with branches array.

---

### 4.4 Update Offer
```
PUT /api/offers/{id}/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Request:** Same as create (include `branch_ids` to update branch assignments).

**Response 200:** Updated offer detail.

---

### 4.5 Delete Offer
```
DELETE /api/offers/{id}/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Response 204:** No content.

---

### 4.6 List All Offers (Admin)
```
GET /api/offers/admin_all/
```
**Auth:** JWT (all staff roles)

**Use:** Returns all offers including inactive, expired, and future ones. For admin panels.

**Response 200:**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "title": "50% Off on All Dairy Products",
      "description": "Get flat 50% off on all dairy items",
      "image": null,
      "start_date": "2026-06-10T00:00:00+05:30",
      "end_date": "2026-06-20T23:59:59+05:30",
      "is_active": true,
      "view_count": 5
    },
    {
      "id": 2,
      "title": "Flat ₹100 Off on Grocery",
      "description": "Expired offer",
      "image": null,
      "start_date": "2026-05-01T00:00:00+05:30",
      "end_date": "2026-05-31T23:59:59+05:30",
      "is_active": false,
      "view_count": 12
    }
  ]
}
```

---

## 5. Banners

### 5.1 List Banners
```
GET /api/banners/
```
**Auth:** Public

**Response 200:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Summer Sale",
      "image": "http://127.0.0.1:8000/media/banners/summer.jpg",
      "link_url": "",
      "linked_offer": 1,
      "order": 1,
      "is_active": true
    },
    {
      "id": 2,
      "title": "New Arrivals",
      "image": "http://127.0.0.1:8000/media/banners/new.jpg",
      "link_url": "https://hypercity.com/new",
      "linked_offer": null,
      "order": 2,
      "is_active": true
    }
  ]
}
```

---

### 5.2 Get Banner Detail
```
GET /api/banners/{id}/
```
**Auth:** Public

**Response 200:**
```json
{
  "id": 1,
  "title": "Summer Sale",
  "image": "http://127.0.0.1:8000/media/banners/summer.jpg",
  "link_url": "",
  "linked_offer": 1,
  "branches": [1, 2],
  "start_date": "2026-06-01T00:00:00+05:30",
  "end_date": "2026-06-30T23:59:59+05:30",
  "is_active": true,
  "order": 1,
  "created_at": "2026-06-01T12:00:00+05:30",
  "updated_at": "2026-06-01T12:00:00+05:30"
}
```

---

### 5.3 Create Banner
```
POST /api/banners/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Request (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | text | Yes | Banner title |
| image | file | Yes | Banner image |
| link_url | text | No | External URL |
| linked_offer | int | No | Offer ID to link |
| branches | list | No | Branch IDs to target |
| start_date | text | No | Schedule start |
| end_date | text | No | Schedule end |
| order | int | No | Display order |
| is_active | bool | No | Default: true |

**Response 201:** Full banner detail.

---

### 5.4 Update Banner
```
PUT /api/banners/{id}/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Response 200:** Updated banner detail.

---

### 5.5 Delete Banner
```
DELETE /api/banners/{id}/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Response 204:** No content.

---

## 6. Notifications

### 6.1 List Notifications
```
GET /api/notifications/
```
**Auth:** JWT

**Response 200:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "New Offer Available!",
      "body": "50% off on all dairy products at Hypercity",
      "image": null,
      "type": "OFFER",
      "linked_offer": 1,
      "is_active": true,
      "sent_at": "2026-06-11T12:00:00+05:30"
    },
    {
      "id": 2,
      "title": "Store Timings Update",
      "body": "All Hypercity stores will remain open until 10 PM this weekend",
      "image": null,
      "type": "COMMON",
      "linked_offer": null,
      "is_active": true,
      "sent_at": "2026-06-10T10:00:00+05:30"
    }
  ]
}
```

---

### 6.2 Create Notification
```
POST /api/notifications/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Request:**
```json
{
  "title": "New Offer Available!",
  "body": "50% off on all dairy products at Hypercity. Visit your nearest store today!",
  "type": "OFFER",
  "linked_offer": 1,
  "target_branches": [1, 2],
  "is_active": true
}
```

**Response 201:**
```json
{
  "id": 1,
  "title": "New Offer Available!",
  "body": "50% off on all dairy products at Hypercity. Visit your nearest store today!",
  "image": null,
  "type": "OFFER",
  "linked_offer": 1,
  "is_active": true,
  "sent_at": "2026-06-11T12:00:00+05:30"
}
```

> **Note:** Creating a notification triggers a Celery task that sends FCM push to all eligible users and creates UserNotification records.

---

### 6.3 Get Notification Detail
```
GET /api/notifications/{id}/
```
**Auth:** JWT

**Response 200:** Full notification detail.

---

### 6.4 Delete Notification
```
DELETE /api/notifications/{id}/
```
**Auth:** JWT (Super Admin / Marketing Manager)

**Response 204:** No content.

---

### 6.5 My Notifications
```
GET /api/notifications/my/
```
**Auth:** JWT

**Use:** Returns the logged-in user's received notifications with read status.

**Response 200:**
```json
{
  "count": 2,
  "results": [
    {
      "id": 1,
      "notification": 1,
      "notification_detail": {
        "id": 1,
        "title": "New Offer Available!",
        "body": "50% off on all dairy products at Hypercity",
        "image": null,
        "type": "OFFER",
        "linked_offer": 1,
        "is_active": true,
        "sent_at": "2026-06-11T12:00:00+05:30"
      },
      "is_read": false,
      "read_at": null
    },
    {
      "id": 2,
      "notification": 2,
      "notification_detail": {
        "id": 2,
        "title": "Store Timings Update",
        "body": "All Hypercity stores will remain open until 10 PM this weekend",
        "image": null,
        "type": "COMMON",
        "linked_offer": null,
        "is_active": true,
        "sent_at": "2026-06-10T10:00:00+05:30"
      },
      "is_read": true,
      "read_at": "2026-06-11T08:00:00+05:30"
    }
  ]
}
```

---

### 6.6 Mark Notification Read
```
POST /api/notifications/mark_read/
```
**Auth:** JWT

**Request:**
```json
{
  "notification_id": 1
}
```

**Response 200:**
```json
{
  "status": "marked as read"
}
```

---

### 6.7 Unread Count
```
GET /api/notifications/unread_count/
```
**Auth:** JWT

**Response 200:**
```json
{
  "unread_count": 3
}
```

---

## 7. Admin Panel

### 7.1 Django Admin
```
GET /admin/
```
Django Admin panel for staff users. Login with phone + password.

### 7.2 Swagger Docs
```
GET /api/docs/
```
Interactive API documentation (Swagger UI).

### 7.3 OpenAPI Schema
```
GET /api/schema/
```
OpenAPI JSON schema.

---

## 8. Staff Management

### 8.1 List Staff
```
GET /api/staff/
```
**Auth:** JWT (Super Admin only)

**Query Parameters:**
| Param | Type | Example | Description |
|-------|------|---------|-------------|
| search | string | `?search=branch` | Search by phone or name |
| ordering | string | `?ordering=-date_joined` | `date_joined`, `-date_joined`, `name`, `-name` |
| page | int | `?page=1` | Page number |

**Response 200:**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "phone": "+919876543210",
      "name": "Branch Manager One",
      "role": "BRANCH_MGR",
      "managed_branch": 1,
      "managed_branch_name": "Hypercity - Koramangala",
      "is_active": true,
      "is_staff": true,
      "date_joined": "2026-06-12T10:00:00+05:30",
      "last_login": null
    },
    {
      "id": 6,
      "phone": "+919876543211",
      "name": "Marketing Manager One",
      "role": "MARKETING",
      "managed_branch": null,
      "managed_branch_name": null,
      "is_active": true,
      "is_staff": true,
      "date_joined": "2026-06-12T11:00:00+05:30",
      "last_login": null
    }
  ]
}
```

**Response 403:**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 8.2 Create Staff
```
POST /api/staff/
```
**Auth:** JWT (Super Admin only)

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| phone | string | Yes | Unique phone number |
| name | string | Yes | Display name |
| password | string | Yes | Login password (hashed on save, not returned) |
| role | string | Yes | `BRANCH_MGR` or `MARKETING` (SUPER_ADMIN not allowed) |
| managed_branch | int | No | Branch ID the manager is assigned to |
| is_active | bool | No | Default: true |

**Validation Rules:**
- `role` must be `BRANCH_MGR` or `MARKETING` — `SUPER_ADMIN` is rejected with error
- `phone` must be unique across all users
- `password` is automatically hashed before saving

**Request Example:**
```json
{
  "phone": "+919876543210",
  "name": "Branch Manager One",
  "password": "securepass123",
  "role": "BRANCH_MGR",
  "managed_branch": 1
}
```

**Response 201:**
```json
{
  "id": 5,
  "phone": "+919876543210",
  "name": "Branch Manager One",
  "role": "BRANCH_MGR",
  "managed_branch": 1,
  "is_active": true
}
```

**Response 400:**
```json
{
  "phone": ["user with this phone already exists."]
}
```

```json
{
  "role": ["Role must be BRANCH_MGR or MARKETING."]
}
```

---

### 8.3 Get Staff Detail
```
GET /api/staff/{id}/
```
**Auth:** JWT (Super Admin only)

**Response 200:**
```json
{
  "id": 5,
  "phone": "+919876543210",
  "name": "Branch Manager One",
  "role": "BRANCH_MGR",
  "managed_branch": 1,
  "managed_branch_name": "Hypercity - Koramangala",
  "is_active": true,
  "is_staff": true,
  "date_joined": "2026-06-12T10:00:00+05:30",
  "last_login": null
}
```

**Response 404:**
```json
{
  "detail": "Not found."
}
```

---

### 8.4 Update Staff
```
PUT /api/staff/{id}/
PATCH /api/staff/{id}/
```
**Auth:** JWT (Super Admin only)

**Request:** Any subset of the create fields. Sending `password` will change it; omitting `password` leaves it unchanged.

**PATCH Request Example:**
```json
{
  "name": "Updated Name",
  "role": "MARKETING",
  "managed_branch": 2,
  "is_active": false
}
```

**Response 200:** Updated staff detail (same format as GET detail).

---

### 8.5 Delete Staff
```
DELETE /api/staff/{id}/
```
**Auth:** JWT (Super Admin only)

**Response 204:** No content.

---

## Quick Reference

### Customer App Flow
```
New User:
1. POST /api/auth/send-otp/        → Send OTP
2. POST /api/auth/signup/          → Verify OTP + create account → Get JWT

Existing User:
1. POST /api/auth/send-otp/        → Send OTP
2. POST /api/auth/verify-otp/      → Verify OTP → Get JWT

3. PUT  /api/profile/              → Save fcm_token for push
4. GET  /api/banners/              → Load carousel
5. GET  /api/offers/               → Load offers list
6. GET  /api/offers/{id}/          → View offer detail
7. GET  /api/notifications/my/     → Check notifications
8. POST /api/notifications/mark_read/ → Mark notification read
```

### Admin Web Flow
```
1. POST   /api/auth/admin-login/     → Login (phone + password)
2. GET    /api/staff/                → View staff users
3. POST   /api/staff/                → Create new staff user
4. PATCH  /api/staff/{id}/           → Update staff role/branch
5. DELETE /api/staff/{id}/           → Remove staff user
6. POST   /api/offers/               → Create offer
7. POST   /api/notifications/        → Send push notification
8. POST   /api/banners/              → Create banner
9. GET    /api/offers/admin_all/     → View all offers
```

---

## Error Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 200 | Success | — |
| 201 | Created | — |
| 204 | Deleted | — |
| 400 | Bad Request | Invalid input, missing fields, validation error |
| 401 | Unauthorized | Invalid token, expired token, wrong credentials |
| 403 | Forbidden | Wrong role (e.g., Marketing trying to delete a user) |
| 404 | Not Found | Wrong ID in URL |
| 500 | Server Error | Check server logs |
