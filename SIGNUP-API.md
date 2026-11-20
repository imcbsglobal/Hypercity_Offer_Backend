# Signup API

## Base URL

```text
https://hs.hypercityllp.in
```

## Endpoint

```text
POST /api/auth/signup/
```

Full URL:

```text
https://hs.hypercityllp.in/api/auth/signup/
```

- **Auth:** Public (no JWT required)
- **Content-Type:** `application/json`
- **OTP:** Not required. The account is created directly.

## Request Body

```json
{
  "phone": "9876543210",
  "first_name": "Asha",
  "last_name": "Kumar",
  "email": "asha@example.com"
}
```

| Field | Type | Required | Rules |
|---|---|:---:|---|
| `phone` | string | Yes | At least 10 characters; only the last 10 digits are stored |
| `first_name` | string | Yes | Max 150 characters; cannot be blank |
| `last_name` | string | Yes | Max 150 characters; cannot be blank |
| `email` | string | Yes | Valid email address; max 254 characters |

## Success Response — `201 Created`

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 5,
    "phone": "9876543210",
    "name": "Asha Kumar",
    "is_customer": true,
    "role": "CUSTOMER"
  }
}
```

`name` is derived automatically from `first_name` and `last_name`.

The new row is stored in the `accounts_user` table with:

- `role = CUSTOMER`
- `is_customer = true`
- `is_staff = false`
- `is_superuser = false`
- no usable password (OTP login only)

## Error Responses

### `400 Bad Request` — invalid phone

```json
{
  "phone": ["Invalid phone number"]
}
```

### `400 Bad Request` — blank first name

```json
{
  "first_name": ["First name cannot be empty"]
}
```

### `400 Bad Request` — blank last name

```json
{
  "last_name": ["Last name cannot be empty"]
}
```

### `400 Bad Request` — invalid email

```json
{
  "email": ["Enter a valid email address."]
}
```

### `400 Bad Request` — account already exists

```json
{
  "error": "Account already exists. Please login."
}
```

## Example

```bash
curl -X POST "https://hs.hypercityllp.in/api/auth/signup/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "first_name": "Asha",
    "last_name": "Kumar",
    "email": "asha@example.com"
  }'
```

## After Signup

The account now exists in `accounts_user`, so the normal OTP login flow works:

1. `POST /api/auth/send-otp/` with `{ "phone": "9876543210" }`
2. `POST /api/auth/verify-otp/` with `{ "phone": "9876543210", "otp": "123456" }`

`send-otp` rejects unknown numbers with:

```json
{
  "error": "Account not found. Please signup first."
}
```
