# Beta Test Plan

This document provides a systematic verification checklist for testing all core user journeys, API endpoints, and system workflows in JyotishAI.

## 1. Authentication Workflows

- [ ] User Registration:
  1. Navigate to `/register`.
  2. Register a new user with valid email, username, and password.
  3. Verify redirection to `/dashboard` upon successful registration.
- [ ] User Login:
  1. Navigate to `/login`.
  2. Enter registered credentials.
  3. Verify JWT cookie is set in browser and dashboard loads.
- [ ] Token Validation & Protected Routes:
  1. Attempt to open `/dashboard` in an incognito window without logging in.
  2. Verify user is redirected to `/login`.

## 2. Birth Chart Calculation

- [ ] Birth Data Entry:
  1. Open `/chart`.
  2. Enter birth date, time, latitude, longitude, and select ayanamsa (`Lahiri`).
  3. Submit calculation form.
- [ ] Chart Rendering Verification:
  1. Confirm Lagna/Ascendant sign and degree match expected ephemeris output.
  2. Switch between North Indian, South Indian, and East Indian chart styles.
  3. Switch between D1 (Rashi), D9 (Navamsha), and D60 (Shastiamsa) divisional charts.
- [ ] Dasha Timeline:
  1. Navigate to `/analysis`.
  2. Confirm active Mahadasha planet and date range display accurately.

## 3. AI Chat & RAG Integration

- [ ] Message Streaming:
  1. Navigate to `/chat`.
  2. Submit query: "What does my active Mahadasha indicate?"
  3. Confirm text streams chunk by chunk into the conversation viewport.
  4. Verify assistant message persists in conversation history.
- [ ] Model Selector Verification:
  1. Open `/settings` -> AI tab.
  2. Change Default Reasoning Model to `OpenRouter — GPT-4o Mini` or `Google Gemini Flash`.
  3. Save settings and submit a new query in `/chat`.
  4. Verify response streams cleanly without errors.

## 4. Document Ingestion & RAG Knowledge Retrieval

- [ ] File Upload:
  1. Navigate to `/documents`.
  2. Upload a sample PDF or TXT file (under 10MB) containing astrological notes.
  3. Confirm initial status badge shows `Pending` -> `Processing` -> `Completed`.
- [ ] Text Preview:
  1. Click Preview (👁️) button on the completed document row.
  2. Verify document metadata and extracted text preview display accurately in the modal.
- [ ] Context Retrieval Test:
  1. Open `/chat`.
  2. Ask a question specific to the content in the uploaded document.
  3. Confirm AI incorporates context retrieved from the vector store in its response.

## 5. History & Session Management

- [ ] Conversation History List:
  1. Open `/history`.
  2. Confirm past conversation titles and timestamps display in chronological order.
  3. Click a conversation item to resume chat and verify past messages load correctly.
- [ ] Delete Conversation:
  1. Click delete action on a conversation item.
  2. Confirm conversation is removed from both history page and chat sidebar.

## 6. Profile & Theme Customization

- [ ] Theme Switching:
  1. Open topbar Theme Toggle menu.
  2. Select `Aurora Forest`, `Solar Ember`, `Celestial Ocean`, or `Royal Ivory`.
  3. Verify color palette updates immediately across all pages.
  4. Reload the page (`F5`) and confirm selected theme remains active.

## 7. Account Logout & Security

- [ ] User Logout:
  1. Click user avatar in topbar and select Logout.
  2. Confirm auth session cookie is cleared and app redirects to `/login`.
  3. Verify back button in browser cannot access protected `/dashboard` state.

## 8. Deployment & Regression Verification

- [ ] System Health Endpoint:
  1. Execute HTTP GET request: `curl http://localhost/api/v1/health`.
  2. Verify JSON response: `{"status": "healthy", ...}` with HTTP 200 code.
- [ ] Container Recovery:
  1. Restart backend container: `docker restart jyotishai-backend`.
  2. Confirm API resumes serving requests within 5 seconds without data loss.
