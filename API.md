# API Documentation

This document describes the public REST API endpoints exposed by JyotishAI at base path `/api/v1`.

## Authentication

### POST `/auth/register`
Registers a new user account.

#### Request Body
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePassword123!",
  "full_name": "John Doe"
}
```

#### Response (201 Created)
```json
{
  "id": "b13a42dd-339e-4f4b-8684-d6920ce77196",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2026-07-24T10:00:00Z"
}
```

---

### POST `/auth/login`
Authenticates user credentials and returns JWT bearer token.

#### Request Body (form-data)
- `username`: `user@example.com`
- `password`: `SecurePassword123!`

#### Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

## Birth Chart & Astrology

### POST `/astrology/calculate`
Calculates planetary positions, houses, nakshatras, and active Mahadasha based on birth parameters.

#### Headers
- `Authorization`: `Bearer <token>`

#### Request Body
```json
{
  "date": "1995-10-25T14:30:00Z",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "timezone": "Asia/Kolkata",
  "ayanamsa": "Lahiri",
  "house_system": "1"
}
```

#### Response (200 OK)
```json
{
  "ascendant": {
    "sign": "Aquarius",
    "degree": 14.52,
    "nakshatra": "Shatabhisha"
  },
  "planets": [
    {
      "name": "Sun",
      "sign": "Libra",
      "degree": 8.12,
      "house": 9,
      "nakshatra": "Swati",
      "is_retrograde": false
    },
    {
      "name": "Moon",
      "sign": "Scorpio",
      "degree": 22.41,
      "house": 10,
      "nakshatra": "Jyeshtha",
      "is_retrograde": false
    }
  ],
  "current_dasha": {
    "planet": "Mercury",
    "start_date": "2021-05-12",
    "end_date": "2038-05-12"
  }
}
```

---

## AI Chat Engine

### POST `/chat/stream`
Streams AI response using Server-Sent Events (SSE).

#### Headers
- `Authorization`: `Bearer <token>`
- `Content-Type`: `application/json`

#### Request Body
```json
{
  "user_query": "What does Saturn placed in my 10th house indicate?",
  "birth_data": {
    "date": "1995-10-25T14:30:00Z",
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "conversation_id": "49ce42c0-2fb2-494a-8082-d52a6dabb009"
}
```

#### Response Stream (200 OK, `text/event-stream`)
```json
{"text": "Saturn ", "finish_reason": null, "conversation_id": null}
{"text": "in the 10th house ", "finish_reason": null, "conversation_id": null}
{"text": "indicates career discipline.", "finish_reason": "stop", "conversation_id": "49ce42c0-2fb2-494a-8082-d52a6dabb009"}
```

---

## Conversations & History

### GET `/conversations`
Retrieves paginated conversation list for authenticated user.

#### Response (200 OK)
```json
[
  {
    "id": "49ce42c0-2fb2-494a-8082-d52a6dabb009",
    "title": "What does Saturn placed in my 10th house...",
    "created_at": "2026-07-24T07:21:29Z",
    "updated_at": "2026-07-24T07:21:30Z"
  }
]
```

---

### GET `/conversations/{conversation_id}`
Retrieves messages for a specific conversation.

#### Response (200 OK)
```json
{
  "id": "49ce42c0-2fb2-494a-8082-d52a6dabb009",
  "title": "What does Saturn placed in my 10th house...",
  "messages": [
    {
      "id": "63807f35-cf2b-4821-969c-c1ad36282335",
      "role": "user",
      "content": "What does Saturn placed in my 10th house indicate?",
      "created_at": "2026-07-24T07:21:30Z"
    },
    {
      "id": "92104f35-cf2b-4821-969c-c1ad36282998",
      "role": "assistant",
      "content": "Saturn in the 10th house indicates career discipline.",
      "created_at": "2026-07-24T07:21:32Z"
    }
  ]
}
```

---

## Document Ingestion & RAG

### POST `/documents/upload`
Uploads a document for background parsing and vector indexing.

#### Form Parameters
- `file`: Multipart file upload (PDF, DOCX, TXT, MD under 10MB)

#### Response (200 OK)
```json
{
  "id": "2750b21947dea2b9f7c76661f167d828",
  "filename": "vedic_astrology_notes.pdf",
  "size_bytes": 1048576,
  "status": "pending",
  "created_at": "2026-07-24T07:18:30Z"
}
```

---

### GET `/documents`
Lists uploaded documents and status for current user.

#### Response (200 OK)
```json
[
  {
    "id": "2750b21947dea2b9f7c76661f167d828",
    "filename": "vedic_astrology_notes.pdf",
    "media_type": "application/pdf",
    "size_bytes": 1048576,
    "status": "completed",
    "created_at": "2026-07-24T07:18:30Z"
  }
]
```

---

## User Profile & Settings

### GET `/users/me`
Retrieves profile and preference settings of the authenticated user.

#### Response (200 OK)
```json
{
  "id": "b13a42dd-339e-4f4b-8684-d6920ce77196",
  "email": "user@example.com",
  "username": "johndoe",
  "full_name": "John Doe",
  "timezone": "Asia/Kolkata",
  "settings": {
    "general": { "theme": "eclipse", "language": "en" },
    "ai": { "default_ai_model": "gemini-flash-latest", "response_length": "medium" }
  }
}
```

---

## System Health

### GET `/health`
Health check endpoint used by reverse proxy and load balancers.

#### Response (200 OK)
```json
{
  "status": "healthy",
  "timestamp": "2026-07-24T12:00:00Z"
}
```
