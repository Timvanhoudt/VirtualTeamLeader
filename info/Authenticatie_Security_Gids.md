# 🔐 Authenticatie & Security Gids 2025

**Educatief document voor RefresCO v2 MLOps Project**
**Datum:** 29 December 2025
**Doel:** Begrijpen welke authenticatie methode past bij jouw situatie

---

## 📚 Inhoudsopgave

1. [Waarom Authenticatie?](#waarom-authenticatie)
2. [Authenticatie Methoden Vergelijking](#authenticatie-methoden-vergelijking)
3. [JWT Tokens (Aanbevolen)](#jwt-tokens-aanbevolen)
4. [Session-Based Authentication](#session-based-authentication)
5. [OAuth 2.0 & Social Login](#oauth-20--social-login)
6. [API Keys](#api-keys)
7. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
8. [Database Schema voor Users](#database-schema-voor-users)
9. [Security Best Practices](#security-best-practices)
10. [Implementatie Plan voor RefresCO v2](#implementatie-plan-voor-refresco-v2)

---

## 🎯 Waarom Authenticatie?

### Huidige Situatie (ONVEILIG!)

Je FastAPI backend heeft nu **geen enkele beveiliging**:

```python
# backend/main.py - regel 41
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ IEDEREEN heeft toegang!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Wat betekent dit?**
- ❌ Iedereen kan analyses bekijken en verwijderen
- ❌ Iedereen kan modellen uploaden en activeren
- ❌ Iedereen kan training data manipuleren
- ❌ Iedereen kan referentie foto's aanpassen
- ❌ Geen logging wie wat deed (geen audit trail)

### Wat als iemand kwaadwillend is?

**Scenario's:**
1. **Data diefstal** - concurrent download al je training data en analyses
2. **Sabotage** - iemand verwijdert al je modellen en training images
3. **Privacy schending** - werknemers foto's worden gestolen (GDPR!)
4. **Valse data** - iemand upload nepdata die je modellen ruïneert

### Wat heb je nodig?

**Basis authenticatie moet kunnen:**
- ✅ Gebruikers laten inloggen met username/password
- ✅ Bijhouden wie is ingelogd (sessie/token)
- ✅ Alleen ingelogde gebruikers toegang geven tot API
- ✅ Uitloggen mogelijk maken

**Advanced (later):**
- ✅ Verschillende rollen (admin, operator, viewer)
- ✅ Permissions per endpoint (wie mag wat?)
- ✅ Audit logging (wie deed wanneer wat?)
- ✅ Password reset functionaliteit

---

## 🔍 Authenticatie Methoden Vergelijking

| Methode | Use Case | Moeilijkheid | Veiligheid | Beste voor |
|---------|----------|--------------|------------|------------|
| **JWT Tokens** | Modern web apps | 🟡 Medium | 🟢 Hoog | SPAs, Mobile apps, APIs |
| **Session Cookies** | Traditional web | 🟢 Makkelijk | 🟢 Hoog | Server-side rendered apps |
| **OAuth 2.0** | Third-party login | 🔴 Complex | 🟢 Zeer hoog | "Login met Google" |
| **API Keys** | Machine-to-machine | 🟢 Makkelijk | 🟡 Medium | Automation, IoT |
| **Basic Auth** | Simpele APIs | 🟢 Zeer makkelijk | 🔴 Laag | Dev/test only |

### Quick Decision Tree

```
Heb je een SPA (Single Page App) zoals React?
├─ JA → JWT Tokens ⭐
└─ NEE → Session Cookies

Wil je "Login met Google/Microsoft"?
├─ JA → OAuth 2.0
└─ NEE → JWT of Sessions

Is dit voor machine-to-machine communicatie?
├─ JA → API Keys
└─ NEE → JWT of Sessions
```

**Voor RefresCO v2 (React SPA):** → **JWT Tokens** ✅

---

## 🎫 JWT Tokens (Aanbevolen)

### Wat is JWT?

**JWT = JSON Web Token**

Een JWT is een **zelf-bevattend token** dat informatie bevat over de gebruiker.

### Hoe werkt het?

```
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│   Browser   │           │   Backend   │           │  Database   │
│  (Frontend) │           │  (FastAPI)  │           │ (PostgreSQL)│
└─────────────┘           └─────────────┘           └─────────────┘
       │                         │                         │
       │  1. POST /login         │                         │
       │  {username, password}   │                         │
       ├────────────────────────>│                         │
       │                         │  2. Verify credentials  │
       │                         ├────────────────────────>│
       │                         │<────────────────────────┤
       │                         │  3. User found + valid  │
       │                         │                         │
       │  4. JWT Token           │                         │
       │  eyJhbGciOiJIUzI1Ni... │                         │
       │<────────────────────────┤                         │
       │                         │                         │
       │  5. GET /api/history    │                         │
       │  Authorization: Bearer  │                         │
       │  eyJhbGciOiJIUzI1Ni... │                         │
       ├────────────────────────>│                         │
       │                         │  6. Verify JWT          │
       │                         │  (no DB call needed!)   │
       │                         │                         │
       │  7. Response data       │                         │
       │<────────────────────────┤                         │
       │                         │                         │
```

### JWT Structuur

Een JWT bestaat uit 3 delen gescheiden door punten:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│─────────── Header ──────────────│─────────────── Payload ────────────────────────────│──────────── Signature ──────────│
```

**1. Header** (algoritme info):
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**2. Payload** (gebruiker data):
```json
{
  "sub": "1234567890",
  "username": "admin",
  "role": "admin",
  "exp": 1735496400  // Vervalt op 29 dec 2025
}
```

**3. Signature** (veiligheid):
```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret_key
)
```

### Voordelen JWT

✅ **Stateless** - Server hoeft geen sessies bij te houden
✅ **Schaalbaar** - Werkt met meerdere servers (load balancing)
✅ **Cross-domain** - Werkt op verschillende domeinen
✅ **Mobile friendly** - Perfect voor apps
✅ **Bevat data** - Username/role zit in token (geen DB call)

### Nadelen JWT

❌ **Kan niet worden ingetrokken** - Token blijft geldig tot expiry
❌ **Groter dan sessie ID** - Meer data per request
❌ **Secret key cruciaal** - Als gelekt, alle tokens invalid

### JWT Best Practices

1. **Korte expiry tijd** - Bijvoorbeeld 15 minuten
2. **Refresh tokens** - Langere geldige tokens om nieuwe access tokens te krijgen
3. **HTTPS verplicht** - Tokens NOOIT over HTTP
4. **Sterke secret** - Minimaal 32 random bytes
5. **Claims valideren** - Altijd exp (expiry) checken

### Code Voorbeeld JWT (FastAPI)

**Backend - Token genereren:**
```python
# backend/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "jouw-super-geheime-key-minimaal-32-characters"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)
```

**Backend - Login endpoint:**
```python
# backend/main.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # 1. Haal user op uit database
    user = get_user_from_db(form_data.username)

    # 2. Verify password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # 3. Maak JWT token
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return {"access_token": access_token, "token_type": "bearer"}
```

**Backend - Protected endpoint:**
```python
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_from_db(username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/api/history")
async def get_history(current_user: User = Depends(get_current_user)):
    # Alleen bereikbaar als user is ingelogd!
    return {"message": f"Hello {current_user.username}"}
```

**Frontend - Login & opslaan token:**
```javascript
// frontend/src/auth.js
async function login(username, password) {
    const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${username}&password=${password}`
    });

    const data = await response.json();

    // Sla token op in localStorage
    localStorage.setItem('access_token', data.access_token);

    return data;
}
```

**Frontend - API calls met token:**
```javascript
// frontend/src/api.js
async function fetchHistory() {
    const token = localStorage.getItem('access_token');

    const response = await fetch('http://localhost:8000/api/history', {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });

    return response.json();
}
```

---

## 🍪 Session-Based Authentication

### Wat zijn Sessions?

**Sessions** gebruiken een **cookie met een session ID** die op de server wordt bijgehouden.

### Hoe werkt het?

```
┌─────────────┐           ┌─────────────┐           ┌─────────────┐
│   Browser   │           │   Backend   │           │   Redis/DB  │
└─────────────┘           └─────────────┘           └─────────────┘
       │                         │                         │
       │  1. POST /login         │                         │
       │  {username, password}   │                         │
       ├────────────────────────>│                         │
       │                         │  2. Verify credentials  │
       │                         │                         │
       │  3. Set-Cookie:         │  4. Store session       │
       │  session_id=abc123      │ ├──────────────────────>│
       │<────────────────────────┤                         │
       │                         │                         │
       │  5. GET /api/history    │                         │
       │  Cookie: session_id=... │                         │
       ├────────────────────────>│  6. Lookup session      │
       │                         ├────────────────────────>│
       │                         │<────────────────────────┤
       │  7. Response data       │  User data              │
       │<────────────────────────┤                         │
```

### Voordelen Sessions

✅ **Kan worden ingetrokken** - Server kan sessie verwijderen (logout werkt direct)
✅ **Kleiner** - Alleen session ID in cookie
✅ **Server controle** - Server bepaalt alles

### Nadelen Sessions

❌ **Stateful** - Server moet sessies bijhouden (memory/database)
❌ **Niet schaalbaar** - Moeilijk met meerdere servers
❌ **Database calls** - Elke request moet sessie opzoeken

### Wanneer Sessions gebruiken?

- Server-side rendered apps (zoals Django, Flask templates)
- Je hebt maar 1 server
- Je wilt volledige controle over sessies

**Voor React SPA:** JWT is beter! ❌

---

## 🔑 OAuth 2.0 & Social Login

### Wat is OAuth 2.0?

**OAuth 2.0** laat gebruikers inloggen met hun **Google/Microsoft/GitHub account**.

### Hoe werkt "Login met Google"?

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │      │ Jouw Backend│      │   Google    │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                     │
       │  1. Click "Login   │                     │
       │     met Google"    │                     │
       ├───────────────────>│                     │
       │                    │  2. Redirect naar   │
       │                    │     Google login    │
       │<───────────────────┤                     │
       │                                          │
       │  3. Login bij Google                    │
       ├────────────────────────────────────────>│
       │                                          │
       │  4. Google stuurt code                  │
       │<────────────────────────────────────────┤
       │                    │                     │
       │  5. Stuur code     │                     │
       │     naar backend   │                     │
       ├───────────────────>│                     │
       │                    │  6. Verwissel code  │
       │                    │     voor token      │
       │                    ├────────────────────>│
       │                    │<────────────────────┤
       │                    │  7. Access token +  │
       │                    │     user info       │
       │  8. Jouw JWT token │                     │
       │<───────────────────┤                     │
```

### Voordelen OAuth 2.0

✅ **Geen password management** - Google doet het werk
✅ **Veilig** - Gebruikers vertrouwen Google meer
✅ **2FA inbegrepen** - Als user 2FA heeft bij Google
✅ **Minder registratie wrijving** - 1 click inloggen

### Nadelen OAuth 2.0

❌ **Complex** - Veel stappen, redirect flows
❌ **Afhankelijk** - Als Google down is, kunnen users niet inloggen
❌ **Privacy** - Google weet welke apps je gebruikt

### Wanneer OAuth gebruiken?

- **Consumer apps** (publieke apps voor eindgebruikers)
- **B2B apps** - "Login met Microsoft Work Account"
- **Open signup** - Iedereen mag account maken

### Wanneer NIET OAuth gebruiken?

- **Interne bedrijfstools** - Je wilt controle over wie mag inloggen
- **Beperkte gebruikers** - Alleen specifieke mensen mogen erin
- **Air-gapped systemen** - Geen internet verbinding

**Voor RefresCO v2:** Waarschijnlijk NIET nodig - het is een interne tool ❌

---

## 🔐 API Keys

### Wat zijn API Keys?

**API Keys** zijn **lange random strings** die je meegeeft per request.

### Hoe werkt het?

```python
# Request met API key
GET /api/history
Headers:
  X-API-Key: sk_live_51H4K3j2eZvKYlo2C8L0F9x...
```

### Voordelen API Keys

✅ **Simpel** - Geen login flow nodig
✅ **Machine-to-machine** - Perfect voor scripts
✅ **Per-key permissions** - Verschillende keys voor verschillende rechten

### Nadelen API Keys

❌ **Geen user context** - Wie gebruikt deze key?
❌ **Moeilijk te roteren** - Als gelekt, moet je overal updaten
❌ **Niet voor browsers** - Keys kunnen worden gestolen uit JavaScript

### Wanneer API Keys gebruiken?

- **Server-to-server** - Andere backend roept jouw API aan
- **IoT devices** - Camera's die foto's uploaden
- **CI/CD pipelines** - Automated deployments

**Voor RefresCO v2:** Mogelijk later voor geautomatiseerde foto uploads 🤔

---

## 👥 Role-Based Access Control (RBAC)

### Wat is RBAC?

**Verschillende gebruikers hebben verschillende rechten.**

### Rollen voor RefresCO v2

| Role | Rechten | Use Case |
|------|---------|----------|
| **Admin** | Alles | IT beheerder, jij |
| **Operator** | Inspecties doen, data corrigeren | Werknemers die systeem gebruiken |
| **Trainer** | Training data beheren, modellen trainen | AI/ML specialist |
| **Viewer** | Alleen analyses bekijken | Management, supervisors |

### Database Schema met Roles

```sql
-- Users tabel
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Mogelijke roles: 'admin', 'operator', 'trainer', 'viewer'
```

### Endpoint Permissions

```python
# Voorbeeld permissions per endpoint
ENDPOINT_PERMISSIONS = {
    "/api/inspect": ["admin", "operator", "trainer"],  # Foto's analyseren
    "/api/history": ["admin", "operator", "trainer", "viewer"],  # Bekijken
    "/api/correct/{id}": ["admin", "operator", "trainer"],  # Data corrigeren
    "/api/workplaces": ["admin"],  # Werkplekken beheren
    "/api/training/*": ["admin", "trainer"],  # Training data
    "/api/models/*": ["admin", "trainer"],  # Model management
}
```

### Code Voorbeeld RBAC

```python
# backend/auth.py
from enum import Enum
from fastapi import HTTPException, status

class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    TRAINER = "trainer"
    VIEWER = "viewer"

def require_role(allowed_roles: list[Role]):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {allowed_roles}"
            )
        return current_user
    return role_checker

# Gebruik in endpoints
@app.delete("/api/workplaces/{workplace_id}")
async def delete_workplace(
    workplace_id: int,
    current_user: User = Depends(require_role([Role.ADMIN]))
):
    # Alleen admins kunnen werkplekken verwijderen
    pass

@app.get("/api/history")
async def get_history(
    current_user: User = Depends(require_role([Role.ADMIN, Role.OPERATOR, Role.VIEWER]))
):
    # Iedereen behalve guests kan history bekijken
    pass
```

---

## 🗄️ Database Schema voor Users

### Complete Users Tabel

```sql
-- PostgreSQL
CREATE TABLE users (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Credentials
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,

    -- Authorization
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,

    -- Metadata
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('admin', 'operator', 'trainer', 'viewer'))
);

-- Indexes voor snelle lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### Audit Log Tabel (Optioneel maar aanbevolen)

```sql
-- Bijhouden WIE WANNEER WAT deed
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(50) NOT NULL,  -- 'login', 'inspect', 'delete', 'train_model'
    resource_type VARCHAR(50),     -- 'analysis', 'workplace', 'model'
    resource_id INTEGER,
    details JSONB,                 -- Extra info als JSON
    ip_address VARCHAR(45),        -- IPv4 of IPv6
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index voor snelle queries
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_action ON audit_log(action);
CREATE INDEX idx_audit_created ON audit_log(created_at);
```

### Voorbeeld Audit Log gebruik

```python
# Na elke belangrijke actie
def log_action(user_id: int, action: str, resource_type: str = None,
               resource_id: int = None, details: dict = None):
    cursor.execute("""
        INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
        VALUES (%s, %s, %s, %s, %s)
    """, (user_id, action, resource_type, resource_id, json.dumps(details)))

# Bij analyse
log_action(
    user_id=current_user.id,
    action="inspect",
    resource_type="workplace",
    resource_id=workplace_id,
    details={"confidence": 0.95, "result": "OK"}
)

# Bij model verwijderen
log_action(
    user_id=current_user.id,
    action="delete_model",
    resource_type="model",
    resource_id=model_id,
    details={"model_name": "werkplek_detector_V3.pt"}
)
```

---

## 🛡️ Security Best Practices

### 1. Password Hashing

**NOOIT plain text passwords opslaan!**

```python
# ❌ FOUT - Plain text
user.password = "admin123"  # NOOIT DOEN!

# ✅ GOED - Hashed met bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
user.hashed_password = pwd_context.hash("admin123")
```

**Waarom bcrypt?**
- Langzaam (goed voor security - moeilijk te bruteforce)
- Salt ingebouwd (elke hash is uniek)
- Adaptive (kan moeilijker worden over tijd)

### 2. Secret Key Management

**NOOIT hard-code secrets!**

```python
# ❌ FOUT
SECRET_KEY = "mijn-geheime-sleutel"

# ✅ GOED - Environment variables
import os
SECRET_KEY = os.getenv("SECRET_KEY")

# .env file (NIET in Git!)
SECRET_KEY=openssl-rand-32-bytes-hier
DATABASE_URL=postgresql://user:pass@localhost/db
```

### 3. HTTPS Overal

```python
# ❌ FOUT
CORS: allow_origins=["http://localhost:3000"]

# ✅ GOED - Development
CORS: allow_origins=["https://localhost:3000"]

# ✅ GOED - Production
CORS: allow_origins=["https://refresco.yourcompany.com"]
```

### 4. Rate Limiting

Voorkom brute-force attacks:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/token")
@limiter.limit("5/minute")  # Max 5 login pogingen per minuut
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    pass
```

### 5. Token Expiry

```python
# ❌ FOUT - Te lang geldig
ACCESS_TOKEN_EXPIRE_MINUTES = 10080  # 1 week

# ✅ GOED - Korte access token + refresh token
ACCESS_TOKEN_EXPIRE_MINUTES = 15      # 15 minuten
REFRESH_TOKEN_EXPIRE_DAYS = 7         # 7 dagen
```

### 6. Input Validation

```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    username: str
    password: str
    email: str

    @validator('username')
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username moet minimaal 3 karakters zijn')
        if not v.isalnum():
            raise ValueError('Username mag alleen letters en cijfers bevatten')
        return v

    @validator('password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password moet minimaal 8 karakters zijn')
        if not any(c.isupper() for c in v):
            raise ValueError('Password moet minimaal 1 hoofdletter bevatten')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password moet minimaal 1 cijfer bevatten')
        return v
```

### 7. SQL Injection Prevention

```python
# ❌ FOUT - SQL Injection mogelijk!
username = request.username
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")

# ✅ GOED - Parameterized queries
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

# ✅ BETER - ORM (SQLAlchemy)
user = db.query(User).filter(User.username == username).first()
```

### 8. CORS Configuration

```python
# ❌ FOUT - Te open
allow_origins=["*"]

# ✅ GOED - Specifieke origins
allow_origins=[
    "https://localhost:3000",           # Development
    "https://refresco.yourcompany.com"  # Production
]
```

---

## 🚀 Implementatie Plan voor RefresCO v2

### Fase 1: Database Setup (1-2 uur)

**Stap 1: PostgreSQL installatie**
```bash
# Windows - Download installer
# https://www.postgresql.org/download/windows/

# Maak database
createdb refresco_mlops

# Maak user
psql -c "CREATE USER refresco_user WITH PASSWORD 'secure_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE refresco_mlops TO refresco_user;"
```

**Stap 2: Users tabel aanmaken**
```sql
-- Connect naar database
psql -d refresco_mlops -U refresco_user

-- Maak users tabel
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'operator',
    is_active BOOLEAN DEFAULT TRUE,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT valid_role CHECK (role IN ('admin', 'operator', 'trainer', 'viewer'))
);

-- Maak eerste admin user
-- Password: admin123 (WIJZIG DIT!)
INSERT INTO users (username, email, hashed_password, role, full_name)
VALUES (
    'admin',
    'admin@refresco.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7f1E.rQkku',
    'admin',
    'System Administrator'
);
```

### Fase 2: Backend Dependencies (10 min)

```bash
cd backend
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

**requirements.txt updaten:**
```txt
fastapi>=0.104.0
uvicorn>=0.24.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
psycopg2-binary>=2.9.9  # PostgreSQL driver
sqlalchemy>=2.0.0        # ORM
```

### Fase 3: Auth Module (2-3 uur)

**Stap 1: Maak auth.py**
```python
# backend/auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os

# Config
SECRET_KEY = os.getenv("SECRET_KEY", "DEV-KEY-CHANGE-IN-PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# User authentication
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Haal user op uit database
    user = get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

# Role checker
def require_role(allowed_roles: list[str]):
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions"
            )
        return current_user
    return role_checker
```

**Stap 2: Update main.py - Login endpoint**
```python
# backend/main.py
from fastapi.security import OAuth2PasswordRequestForm
from auth import (
    verify_password, create_access_token,
    get_current_user, require_role,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify credentials
    user = get_user_by_username(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    update_last_login(user.id)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name
        }
    }

# Protect endpoints
@app.get("/api/history")
async def get_history(current_user = Depends(get_current_user)):
    # Nu alleen toegankelijk voor ingelogde users!
    pass

@app.delete("/api/workplaces/{workplace_id}")
async def delete_workplace(
    workplace_id: int,
    current_user = Depends(require_role(["admin"]))
):
    # Alleen admins!
    pass
```

### Fase 4: Frontend Login (2-3 uur)

**Stap 1: Login Component**
```javascript
// frontend/src/Login.js
import React, { useState } from 'react';
import axios from 'axios';

function Login({ onLoginSuccess }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // OAuth2 verwacht form data
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await axios.post('http://localhost:8000/token', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            // Sla token op
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('user', JSON.stringify(response.data.user));

            // Callback naar App
            onLoginSuccess(response.data.user);
        } catch (err) {
            setError('Ongeldige gebruikersnaam of wachtwoord');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-container">
            <h2>RefresCO v2 - Login</h2>
            <form onSubmit={handleLogin}>
                <input
                    type="text"
                    placeholder="Gebruikersnaam"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Wachtwoord"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Inloggen...' : 'Login'}
                </button>
                {error && <p className="error">{error}</p>}
            </form>
        </div>
    );
}

export default Login;
```

**Stap 2: Axios Interceptor (Auto token toevoegen)**
```javascript
// frontend/src/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
    baseURL: API_URL
});

// Add token to every request
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Handle 401 (unauthorized) responses
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Token expired or invalid - logout
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
```

**Stap 3: Update App.js**
```javascript
// frontend/src/App.js
import React, { useState, useEffect } from 'react';
import Login from './Login';
import InspectView from './InspectView';  // Je huidige app
import api from './api';

function App() {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const handleLogin = (userData) => {
        setUser(userData);
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        setUser(null);
    };

    if (loading) {
        return <div>Laden...</div>;
    }

    if (!user) {
        return <Login onLoginSuccess={handleLogin} />;
    }

    return (
        <div>
            <div className="header">
                <span>Ingelogd als: {user.full_name} ({user.role})</span>
                <button onClick={handleLogout}>Uitloggen</button>
            </div>
            <InspectView user={user} />
        </div>
    );
}

export default App;
```

### Fase 5: Testing (1 uur)

**Test scenario's:**

1. **Login met correcte credentials** → ✅ Succesvol
2. **Login met verkeerde password** → ❌ Error message
3. **Access protected endpoint zonder token** → ❌ 401 Unauthorized
4. **Access protected endpoint met token** → ✅ Data ontvangen
5. **Token expiry** → ❌ 401, redirect naar login
6. **Role-based access** → Admin kan alles, operator beperkt

---

## 📋 Checklist: Is je authenticatie veilig?

- [ ] Passwords worden gehashed met bcrypt (niet plain text)
- [ ] SECRET_KEY zit in environment variables (niet hardcoded)
- [ ] JWT tokens hebben korte expiry tijd (max 30 min)
- [ ] HTTPS wordt gebruikt (geen HTTP)
- [ ] CORS is geconfigureerd (niet allow_origins=["*"])
- [ ] Rate limiting op login endpoint (max 5 pogingen/minuut)
- [ ] Input validation (username, password requirements)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Audit logging (wie deed wat wanneer)
- [ ] Logout functionaliteit werkt (token wordt verwijderd)

---

## 🎓 Samenvatting

### Wat je nu weet:

1. **JWT vs Sessions** - JWT is beter voor React SPAs
2. **OAuth 2.0** - Voor "Login met Google" (niet nodig voor interne tool)
3. **RBAC** - Verschillende rollen (admin, operator, viewer)
4. **Security best practices** - Password hashing, HTTPS, rate limiting
5. **Database schema** - Users tabel + audit logging

### Wat we gaan bouwen:

- ✅ JWT-based authentication
- ✅ PostgreSQL users tabel
- ✅ Role-based access control (admin/operator/trainer/viewer)
- ✅ Login/logout functionaliteit
- ✅ Protected API endpoints
- ✅ Frontend login scherm

### Totale tijd: ~9-12 uur

1. PostgreSQL setup (1-2 uur)
2. Backend auth (2-3 uur)
3. Frontend login (2-3 uur)
4. Testing & fixes (1-2 uur)
5. Database migratie SQLite → PostgreSQL (3-4 uur)

---

## 📚 Verder lezen

- [JWT.io - JWT Debugger](https://jwt.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth 2.0 Simplified](https://aaronparecki.com/oauth-2-simplified/)

---

**Klaar om te beginnen? Volgende stap: PostgreSQL migratie!**
