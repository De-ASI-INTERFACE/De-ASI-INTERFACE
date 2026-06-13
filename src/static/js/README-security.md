# Security Patch Notes — SEC-001 through SEC-014

> Branch: `security/patch-sec-001-014`  
> Date: 2026-06-12  
> Auditor: De-ASI Security Review  

## Summary

| ID | Severity | Title | Status |
|---|---|---|---|
| SEC-001 | CRITICAL | JWT token in global JS scope | ✅ Fixed — httpOnly cookie auth |
| SEC-002 | CRITICAL | No HTTP status code validation | ✅ Fixed — response.ok checks everywhere |
| SEC-003 | CRITICAL | Stored XSS via innerHTML | ✅ Fixed — DOMPurify.sanitize() + textContent |
| SEC-004 | CRITICAL | No CSRF protection | ✅ Fixed — X-CSRF-Token header on all POSTs |
| SEC-005 | HIGH | 2FA client-side only | ✅ Fixed — client check is UX only; server enforces |
| SEC-006 | HIGH | Stored XSS via conversation title | ✅ Fixed — DOM construction via textContent |
| SEC-007 | HIGH | WebSocket unauthenticated | ✅ Fixed — WS ticket endpoint, server validates |
| SEC-008 | HIGH | diagnose=True leaks secrets in prod | ✅ Fixed — gated on ENVIRONMENT != production |
| SEC-009 | MEDIUM | Links missing rel=noopener noreferrer | ✅ Fixed — added to all auto-links |
| SEC-010 | MEDIUM | Logout doesn't block on server invalidation | ✅ Fixed — hard dependency on server response |
| SEC-011 | MEDIUM | Logs written to relative path | ✅ Fixed — absolute LOG_DIR from settings |
| SEC-012 | MEDIUM | api_used exposed to client | ✅ Fixed — removed from client response |
| SEC-013 | INFO | loadConversation() unimplemented | ✅ Fixed — full implementation added |
| SEC-014 | INFO | Date.now() ID collision risk | ✅ Fixed — crypto.randomUUID() |

## Required Backend Changes

These frontend patches require corresponding server-side changes:

### 1. httpOnly Cookie Auth (SEC-001)
```python
# On successful 2FA verification:
response.set_cookie(
    'auth_token',
    value=jwt_token,
    httponly=True,       # Not accessible from JS
    secure=True,         # HTTPS only
    samesite='Strict',   # CSRF protection
    max_age=3600         # 1 hour expiry
)
```

### 2. CSRF Token Endpoint (SEC-004)
```python
@app.get('/api/auth/csrf-token')
async def get_csrf_token(response: Response):
    token = secrets.token_hex(32)
    response.set_cookie('csrf_token', token, samesite='Strict', secure=True)
    return {'csrf_token': token}

# Validate on every state-changing route:
def validate_csrf(request: Request):
    header_token = request.headers.get('X-CSRF-Token')
    cookie_token = request.cookies.get('csrf_token')
    if not header_token or header_token != cookie_token:
        raise HTTPException(status_code=403, detail='CSRF validation failed')
```

### 3. 2FA Rate Limiting (SEC-005)
```python
# Max 5 attempts per username per 15 minutes
@app.post('/api/auth/verify-2fa')
@rate_limit(max_attempts=5, window_seconds=900, key='username')
async def verify_2fa(request: Verify2FARequest):
    ...
```

### 4. WebSocket Ticket Endpoint (SEC-007)
```python
@app.post('/api/auth/ws-ticket')
async def get_ws_ticket(current_user = Depends(get_current_user)):
    # Short-lived ticket (30s TTL), single-use
    ticket = secrets.token_urlsafe(32)
    redis.setex(f'ws_ticket:{ticket}', 30, current_user.id)
    return {'ticket': ticket}
```

### 5. Logger Environment Variable (SEC-008, SEC-011)
Add to your `.env` / Railway environment variables:
```
ENVIRONMENT=production
LOG_LEVEL=INFO
LOG_DIR=/var/log/app
```

### 6. Install DOMPurify (SEC-003)
Add to your HTML before `app.js`:
```html
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"
        integrity="sha384-..." crossorigin="anonymous"></script>
```
Or install as a package:
```bash
npm install dompurify
```
