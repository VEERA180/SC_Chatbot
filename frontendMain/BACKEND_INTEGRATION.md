# VGIMT AI Assistant - Backend Integration Guide

This document provides all the necessary information to connect the VGIMT AI Assistant frontend to your backend API.

---

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [API Endpoints](#api-endpoints)
3. [Request/Response Formats](#requestresponse-formats)
4. [Source Object Structure](#source-object-structure)
5. [Error Handling](#error-handling)
6. [Session Management](#session-management)
7. [Testing the Integration](#testing-the-integration)

---

## Environment Configuration

### Setting the Backend URL

Create a `.env` file in the frontend root directory:

```env
REACT_APP_API_URL=http://your-backend-url:8000
```

**Default:** If not set, the frontend defaults to `http://localhost:8000`

### Available Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API base URL | `http://localhost:8000` |

---

## API Endpoints

The frontend expects the following endpoints from the backend:

### 1. Health Check

```
GET /health
```

**Purpose:** Check if the backend is online

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-03T12:00:00Z"
}
```

### 2. Send Message (Chat)

```
POST /api/chat
```

**Purpose:** Send a user question and receive an AI-generated response

**Request Body:**
```json
{
  "question": "How do I unlock a user in GRC?",
  "conversation_id": "session_1706972800000_abc123def",
  "user_id": "anonymous"
}
```

**Expected Response:**
```json
{
  "answer": "## How to Unlock a User in GRC\n\nTo unlock a user...",
  "sources": [
    {
      "id": 1,
      "title": "How to Unlock User in GRC.pptx",
      "page": 4,
      "location": "sites/unit-vgimt/VGIMT solution/End User Instructions/How to Unlock User in GRC.pptx",
      "url": "https://volvogroup.sharepoint.com/sites/unit-vgimt/..."
    }
  ],
  "top_sources_formatted": "Optional formatted string of sources",
  "type": "rag",
  "error": null
}
```

### 3. Clear Session

```
POST /api/session/{session_id}/clear
```

**Purpose:** Clear conversation history for a session

**Expected Response:**
```json
{
  "success": true,
  "message": "Session cleared successfully"
}
```

### 4. Get Session Stats (Optional)

```
GET /api/session/{session_id}/stats
```

**Purpose:** Get statistics about the current session

**Expected Response:**
```json
{
  "session_id": "session_1706972800000_abc123def",
  "message_count": 5,
  "created_at": "2026-02-03T10:00:00Z",
  "last_activity": "2026-02-03T12:30:00Z"
}
```

---

## Request/Response Formats

### Chat Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The user's question |
| `conversation_id` | string | Yes | Unique session identifier |
| `user_id` | string | No | User identifier (defaults to "anonymous") |

### Chat Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answer` | string | Yes | Markdown-formatted response from the LLM |
| `sources` | array | Yes | Array of source objects (can be empty) |
| `top_sources_formatted` | string | No | Pre-formatted sources string |
| `type` | string | No | Response type ("rag", "general", "error") |
| `error` | string | No | Error message if any |

---

## Source Object Structure

Each source in the `sources` array should have the following structure:

```typescript
interface Source {
  id: number | string;           // Unique identifier
  title: string;                 // Document filename (e.g., "Guide.pptx")
  page?: number;                 // Page number (optional)
  location: string;              // Full path in SharePoint
  url: string;                   // Direct URL to open the document
  relevance?: number;            // Relevance score 0-1 (optional)
}
```

### Example Source Object

```json
{
  "id": 1,
  "title": "How to Unlock User in GRC.pptx",
  "page": 4,
  "location": "sites/unit-vgimt/VGIMT solution/End User Instructions/How to Unlock User in GRC.pptx",
  "url": "https://volvogroup.sharepoint.com/sites/unit-vgimt/VGIMT%20solution/End%20User%20Instructions/How%20to%20Unlock%20User%20in%20GRC.pptx",
  "relevance": 0.95
}
```

### Supported File Types

The UI displays different colors for file icons based on extension:

| Extension | Color |
|-----------|-------|
| `.pptx`, `.ppt` | Orange |
| `.pdf` | Red |
| `.docx`, `.doc` | Blue |
| `.xlsx`, `.xls` | Green |
| Other | Gray |

---

## Error Handling

### HTTP Error Responses

The frontend handles errors gracefully. Your backend should return appropriate HTTP status codes:

| Status Code | Description | Frontend Behavior |
|-------------|-------------|-------------------|
| 200 | Success | Display response |
| 400 | Bad Request | Show error message |
| 401 | Unauthorized | Show error message |
| 500 | Server Error | Show error message |
| Timeout | No response in 60s | Show connection error |

### Error Response Format

```json
{
  "detail": "Error message to display to user",
  "message": "Alternative error message field"
}
```

The frontend checks for `detail` first, then `message`.

---

## Session Management

### How Sessions Work

1. **Session Creation:** A unique session ID is generated when the user first visits
2. **Session Storage:** Stored in browser's `sessionStorage`
3. **Session Format:** `session_{timestamp}_{random_string}`
4. **New Chat:** Clicking "New chat" creates a new session ID

### Session ID Example

```
session_1706972800000_x7k9m2pqr
```

---

## Testing the Integration

### 1. Start your backend

```bash
# Your backend should be running at the configured URL
python main.py  # or your backend start command
```

### 2. Start the frontend

```bash
cd frontend
npm start
```

### 3. Verify health check

Open browser console and check for:
- ✅ No "Backend health check failed" error
- ✅ No offline indicator at bottom of screen

### 4. Test chat flow

1. Type a message and press Enter or click Send
2. Verify the loading skeleton appears
3. Verify the response is displayed with markdown formatting
4. Click "Sources" button to verify sources sidebar opens

---

## Frontend API Service Location

All API calls are made from:

```
src/services/api.js
```

### Key Functions

```javascript
// Send a message
chatService.sendMessage(question, userId)

// Health check
chatService.healthCheck()

// Clear session
chatService.clearSession()

// Create new session
chatService.createNewSession()

// Get current session ID
chatService.getCurrentSessionId()
```

---

## CORS Configuration

Ensure your backend allows requests from the frontend origin:

```python
# Example for FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Markdown Support

The frontend renders markdown in responses. Supported features:

- **Headings** (H1-H4)
- **Bold** and *italic* text
- Bullet and numbered lists
- Code blocks with syntax highlighting
- Tables (GitHub Flavored Markdown)
- Links (open in new tab)
- Blockquotes
- Horizontal rules

---

## Quick Checklist

Before going live, ensure:

- [ ] Backend URL is configured in `.env`
- [ ] `/health` endpoint returns 200
- [ ] `/api/chat` accepts POST with correct payload
- [ ] Response includes `answer` and `sources` fields
- [ ] Sources have `title`, `location`, and `url` fields
- [ ] CORS is properly configured
- [ ] Error responses include `detail` or `message` field

---

## Support

For issues or questions about the frontend integration, check the component files:

- `src/App.js` - Main application logic
- `src/services/api.js` - API service layer
- `src/components/MessageBubble.jsx` - Message display with markdown
- `src/components/SourcesSidebar.jsx` - Sources sidebar display
