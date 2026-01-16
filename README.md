# Blue Academy – Pre‑Sales Agent API

This repository contains the **Pre‑Sales Chatbot API** developed for **Blue Academy**, built using **FastAPI**. The service powers an intelligent conversational agent used for course discovery, pre‑sales assistance, and contextual guidance via an embeddable chat widget.

---

## Features

* Embeddable chat widget for frontend integration
* Session‑based chat history management
* Context‑aware responses using page and user context
* Internal synchronization with MongoDB and Weaviate
* Cache pre‑warming for low‑latency contextual resolution

---

## Tech Stack

* **Python**
* **FastAPI**
* **Uvicorn**
* **MongoDB** (source of truth)
* **Weaviate** (vector store / hybrid search)
* **Docker** (optional deployment)
* **OpenAI agent SDK** (Agent Development)
---

## Project Setup

### Prerequisites

* Python 3.10+
* Virtual environment (recommended)
* Docker (optional)

---

## Environment Configuration

Create a `.env` file using the provided example:

```bash
  cp .env.example .env
```

Populate the required environment variables as per your deployment setup (database URLs, API keys, etc.).

---

## Running the Application

### Option 1: Run using Python

```bash
  python -m main.py
```

### Option 2: Run using Uvicorn

```bash
  uvicorn main:app --port <PORT>
```

Replace `<PORT>` with any desired port number.

### Docker

If running via Docker, the application is exposed on:

```
http://localhost:5000
```

---

## Public Endpoints

### 1. Chat Widget Script

**Endpoint**

```
GET /chat-widget/chat-widget.js
```

**Description**

* Direct embeddable JavaScript file
* Intended to be injected into any HTML page
* Bootstraps the Blue Data Academy chat widget

---

### 2. Fetch Chat History

**Endpoint**

```
GET /agent/chat/history/{session_id}
```

**Description**

* Fetches full chat history for a session
* Used to restore conversation state

**Path Parameter**

* `session_id`: `string | UUID` (dynamic per user/session)

**Response Format**

```json
[
  {
    "role": "user | assistant",
    "content": "string"
  }
]
```

---

### 3. Chat With History (Primary Chat Endpoint)

**Endpoint**

```
POST /agent/chat/v2/with_history
```

**Request Body Schema**

```json
{
  "message": "string",
  "session_id": "string | uuid",
  "context": {
    "page_context": {
      "url": "string",
      "title": "string"
    },
    "user_context": {
      "action": "string",
      "course": {
        "id": "courseId",
        "title": "courseTitle",
        "slug": "courseSlug"
      }
    }
  }
}
```

**Notes**

* `context` is **optional**
* Used to provide page‑level and user‑level signals to the agent

**Response Schema**

```json
{
  "reply": "AgentResponse",
  "session_id": "same_as_input"
}
```

---

## Internal Endpoints (System Use Only)

> These endpoints are intended for internal services and background workflows.

---

### 1. Sync Mongo Data to Weaviate

**Endpoint**

```
GET /internal/sync/mongo_data
```

**Description**

* Syncs course and content data from MongoDB
* Updates vector embeddings in Weaviate
* Typically triggered manually or via scheduled jobs

---

### 2. Cache Page Context (Pre‑Warm Cache)

**Endpoint**

```
POST /internal/cache/page
```

**Purpose**

* Pre‑warms cache whenever a course page is rendered on the frontend
* Avoids redundant MongoDB lookups by the agent
* Improves response latency and ensures idempotent behavior

**Request Body**

```json
{
  "slug": "courseSlug",
  "data": "complete MongoDB course document"
}
```

**Usage Scenario**

* Called by frontend/backend when a course detail page loads
* Enables the agent to immediately resolve page context

---

## Notes & Best Practices

* Always reuse `session_id` for a single user session to maintain conversational continuity
* Pre‑warm cache for course pages to minimize agent latency
* Internal endpoints should be protected via network or auth rules in production

---

## License

Internal – Blue Data Academy
