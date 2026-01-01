# 🗄️ Databases Uitleg - SQLite vs MySQL vs PostgreSQL

**Voor:** RefresCO v2 - AI Werkplek Inspectie Systeem
**Datum:** 29 December 2025
**Doel:** Begrijpen welke database geschikt is voor welke situatie

---

## 📚 Inhoudsopgave

1. [Wat is een Database?](#wat-is-een-database)
2. [SQLite vs PostgreSQL - Vergelijking](#sqlite-vs-postgresql)
3. [MySQL vs PostgreSQL](#mysql-vs-postgresql)
4. [Management Tools](#management-tools)
5. [Wanneer Welke Database?](#wanneer-welke-database)
6. [Migratie Strategie](#migratie-strategie)

---

## Wat is een Database?

### Database Types

**Embedded Database (SQLite):**
```
Application ─→ [SQLite] ─→ database.db (bestand)
                ↑
           Geen server!
```

**Client-Server Database (MySQL/PostgreSQL):**
```
Application ─→ [Database Server] ─→ Data Storage
    ↑              ↑
TCP/IP        Runs 24/7
```

---

## SQLite vs PostgreSQL

### 🔴 1. CONCURRENCY (Gelijktijdige Toegang)

#### SQLite: 1 Schrijver Tegelijk ❌

**Hoe SQLite werkt:**
```python
# User 1 start een write operatie
cursor.execute("INSERT INTO analyses ...")
# 🔒 Database is nu LOCKED

# User 2 probeert tegelijk te schrijven
cursor.execute("INSERT INTO analyses ...")
# ⏳ WACHT... tot User 1 klaar is
# Of krijgt: "database is locked" error
```

**Probleem in productie:**
```
Scenario: 5 operators maken tegelijk een foto-inspectie

Tijd →
User 1: |████████| INSERT analyse (200ms)
User 2:          |⏳⏳⏳⏳████████| WACHT... dan INSERT (400ms)
User 3:                    |⏳⏳⏳⏳⏳⏳████████| WACHT... (600ms)
User 4:                              |⏳⏳⏳⏳⏳⏳⏳⏳████████| (800ms)
User 5:                                        |⏳⏳⏳⏳⏳⏳⏳⏳⏳⏳████| (1000ms!)

Resultaat: User 5 wacht 1 seconde! ⏱️
```

#### PostgreSQL: Meerdere Schrijvers Tegelijk ✅

**Hoe PostgreSQL werkt (MVCC):**
```python
# User 1 schrijft
cursor.execute("INSERT INTO analyses ...")

# User 2 schrijft TEGELIJKERTIJD
cursor.execute("INSERT INTO analyses ...")
# ✅ Geen wachten! Beide gebeuren parallel
```

**In productie:**
```
Scenario: 5 operators tegelijk

User 1: |████████| INSERT (200ms)
User 2: |████████| INSERT (200ms)  ← Parallel!
User 3: |████████| INSERT (200ms)  ← Parallel!
User 4: |████████| INSERT (200ms)  ← Parallel!
User 5: |████████| INSERT (200ms)  ← Parallel!

Resultaat: Allemaal 200ms! 🚀
```

**Impact voor jouw app:**
```python
# Backend endpoint: /api/inspect
@app.post("/api/inspect")
async def inspect(file: UploadFile, workplace_id: int):
    # 1. YOLO inference (500ms)
    result = yolo_model.predict(image)

    # 2. Database INSERT
    save_analysis(result)

    return result

# Met SQLite (10 gelijktijdige requests):
# → Mogelijk 5-10 seconden wachttijd
# → Users zien "Loading..." heel lang

# Met PostgreSQL (10 gelijktijdige requests):
# → Elk 500ms
# → Snelle response voor iedereen
```

---

### 🌐 2. NETWORK ACCESS

#### SQLite: Alleen Lokaal ❌

```
SQLite is een FILE - geen server!

backend/data/analyses.db ← Dit is gewoon een bestand
                          ← Moet op DEZELFDE computer als backend
```

**Probleem bij schalen:**
```
Je wilt 2 backend servers:

[Server 1 (FastAPI)]  →  database1.db  ❌
[Server 2 (FastAPI)]  →  database2.db  ❌

→ 2 aparte databases!
→ Data is NIET gedeeld
→ User op Server 1 ziet niet wat User op Server 2 doet
```

#### PostgreSQL: Network Server ✅

```
PostgreSQL is een DATABASE SERVER

┌─────────────┐
│ PostgreSQL  │  ← Draait apart
│   Server    │     Op eigen machine/container
└─────────────┘
      ↑ ↑ ↑
      │ │ │ Network connections (TCP/IP)
      │ │ │
  ┌───┘ │ └───┐
  │     │     │
[API1] [API2] [API3]  ← Alle backends delen zelfde data
```

**Configuratie:**
```python
# Alle servers gebruiken DEZELFDE database
DATABASE_URL = "postgresql://user:pass@db-server:5432/refresco"

# Server 1 (Europa)
engine = create_engine(DATABASE_URL)

# Server 2 (Amerika)
engine = create_engine(DATABASE_URL)

# Server 3 (Azië)
engine = create_engine(DATABASE_URL)

→ Alle 3 gebruiken DEZELFDE database
→ Data is consistent overal
→ Perfect voor load balancing
```

---

### 📊 3. DATA TYPES & FEATURES

#### SQLite: Beperkt ❌

**Slechts 5 data types:**
```sql
SQLite types:
- NULL
- INTEGER
- REAL (float)
- TEXT
- BLOB

Geen:
❌ BOOLEAN (gebruikt 0/1)
❌ DATE/DATETIME (opgeslagen als TEXT/INT)
❌ JSON (wel vanaf versie 3.38, maar basic)
❌ ARRAY
❌ UUID
```

**Timestamp probleem:**
```python
# Je wilt een timestamp opslaan
import datetime

# SQLite:
timestamp = datetime.now().isoformat()  # "2025-12-29T15:30:00"
cursor.execute("INSERT INTO analyses (timestamp) VALUES (?)",
               (timestamp,))  # Opgeslagen als TEXT

# Probleem: sorteer/filter = LANGZAAM
cursor.execute("""
    SELECT * FROM analyses
    WHERE timestamp > '2025-12-01'
    ORDER BY timestamp DESC
""")  # String vergelijking! Niet geoptimaliseerd
```

**JSON support:**
```python
# Model config opslaan
config = {
    'model_type': 'classification',
    'confidence_threshold': 0.7,
    'classes': ['OK', 'NOK']
}

# SQLite: Convert naar string
import json
config_str = json.dumps(config)
cursor.execute("INSERT INTO models (config) VALUES (?)",
               (config_str,))

# Query binnen JSON? Moet in Python:
cursor.execute("SELECT config FROM models")
for row in cursor.fetchall():
    cfg = json.loads(row[0])  # Parse in Python
    if cfg['confidence_threshold'] > 0.5:  # Filter in Python
        # ...
```

#### PostgreSQL: Volledig ✅

**70+ data types:**
```sql
PostgreSQL ondersteunt:
✅ Boolean
✅ Smallint, Integer, Bigint
✅ Real, Double Precision, Numeric
✅ Date, Time, Timestamp, Interval
✅ UUID
✅ JSON, JSONB (binary JSON - snel!)
✅ Array
✅ Geometric types (Point, Line, Circle)
✅ Network types (inet, cidr, macaddr)
✅ Text search types
✅ XML
✅ Custom types (maak je eigen!)
```

**Native JSON:**
```python
# PostgreSQL: Native JSON type
from sqlalchemy.dialects.postgresql import JSONB

cursor.execute("INSERT INTO models (config) VALUES (%s)",
               (Json(config),))

# Query binnen JSON? Direct in SQL:
cursor.execute("""
    SELECT * FROM models
    WHERE config->>'model_type' = 'classification'
    AND (config->>'confidence_threshold')::float > 0.5
""")  # Filter in database! Veel sneller
```

**Arrays:**
```python
# Detection results met meerdere objecten
detections = [
    {'class': 'hamer', 'bbox': [10, 20, 50, 60]},
    {'class': 'schaar', 'bbox': [100, 120, 150, 160]}
]

# PostgreSQL: Native array support
CREATE TABLE detections (
    id SERIAL,
    objects TEXT[],
    bboxes INTEGER[][]
);

# SQLite: Moet als JSON string of aparte tabel
```

---

### 💾 4. BACKUP & RECOVERY

#### SQLite: Simpel maar Gevaarlijk ❌

```bash
# Backup = kopieer bestand
cp backend/data/analyses.db backup/analyses_20251229.db

# Probleem 1: Tijdens gebruik?
# → Als backend schrijft tijdens copy = CORRUPTED backup! 💥

# Probleem 2: Restore?
# → Stop backend
# → Kopieer backup terug
# → Start backend
# → Downtime!
```

**WAL mode (Write-Ahead Logging):**
```python
conn = sqlite3.connect('analyses.db')
conn.execute("PRAGMA journal_mode=WAL")

# Nu heb je 3 bestanden:
# - analyses.db
# - analyses.db-wal  (write ahead log)
# - analyses.db-shm  (shared memory)

# Backup moet ALLE 3 kopiëren op exact zelfde moment
# Anders: inconsistent backup
```

#### PostgreSQL: Enterprise-Grade ✅

**Continuous Archiving:**
```bash
# PostgreSQL logt ELKE verandering

# Backup tijdens productie (geen downtime):
pg_basebackup -D /backup -Ft -z -P

# Voordeel:
# ✅ Kan terugzetten naar EXACT tijdstip
# ✅ Geen downtime tijdens backup
# ✅ Automatische consistency
```

**Point-in-Time Recovery:**
```bash
# Scenario: Operator verwijdert per ongeluk 100 analyses om 10:15

# Met SQLite:
# → Restore laatste backup (van vannacht 00:00)
# → Verlies ALLE data van vandaag 💥

# Met PostgreSQL:
pg_restore --target-time="2025-12-29 10:14:00"
# → Database is terug naar 10:14, voor de delete!
# → Alleen 1 minuut data verlies ✅
```

**Streaming Replication:**
```
Primary Server  ──streaming──> Standby Server
(Production)                    (Hot backup)

Als Primary crashed:
→ Promote Standby to Primary (< 1 min)
→ Bijna geen data loss
→ Automatische failover mogelijk
```

---

### 🔐 5. USER MANAGEMENT & SECURITY

#### SQLite: Geen ❌

```python
# SQLite heeft GEEN gebruikers/permissions
# Iedereen met toegang tot bestand heeft VOLLEDIGE toegang

# "Security" = OS file permissions
chmod 600 analyses.db  # Alleen jouw user

# Probleem:
# → Backend draait als user 'www-data'
# → Kan ALLES: SELECT, INSERT, UPDATE, DELETE, DROP TABLE
# → Geen granulaire controle
```

**Geen audit log:**
```
Vraag: Wie heeft deze analyse verwijderd?
Antwoord: SQLite weet het niet 🤷‍♂️

→ Moet zelf audit tabel bouwen
→ Extra code, extra werk
```

#### PostgreSQL: Volledig ✅

**Gebruikers met rechten:**
```sql
-- 1. Admin (alles)
CREATE USER admin_user WITH PASSWORD 'secure123';
GRANT ALL PRIVILEGES ON DATABASE refresco TO admin_user;

-- 2. Backend API (read/write analyses)
CREATE USER api_user WITH PASSWORD 'api123';
GRANT SELECT, INSERT, UPDATE ON analyses TO api_user;
GRANT SELECT ON workplaces TO api_user;
-- GEEN DELETE of DROP rechten!

-- 3. Readonly (voor analytics/reports)
CREATE USER analytics_user WITH PASSWORD 'analytics123';
GRANT SELECT ON ALL TABLES TO analytics_user;
-- Kan NIETS wijzigen

-- 4. Backup user
CREATE USER backup_user WITH PASSWORD 'backup123';
GRANT pg_read_all_data TO backup_user;
```

**Row-level security:**
```sql
-- Operators zien alleen hun eigen werkplek data

CREATE POLICY operator_policy ON analyses
FOR SELECT
USING (workplace_id IN (
    SELECT id FROM workplaces
    WHERE assigned_to = current_user
));

-- User 'operator1' ziet alleen zijn eigen analyses
-- User 'operator2' ziet andere analyses
```

**Audit logging:**
```sql
-- Built-in audit trail
ALTER DATABASE refresco SET log_statement = 'all';

-- Logs tonen:
-- 2025-12-29 15:30:45 [user=api_user] DELETE FROM analyses WHERE id=123
-- → Weet wie, wat, wanneer
```

---

### ⚡ 6. PERFORMANCE & INDEXING

#### SQLite: Basic ❌

```python
# Complexe query
SELECT * FROM analyses
WHERE workplace_id = 1
  AND timestamp > '2025-12-01'
  AND predicted_class = 0
ORDER BY confidence DESC
LIMIT 10

# SQLite kan maar 1 index per query gebruiken
# → Kiest workplace_id index
# → Filtert rest in memory (LANGZAAM bij veel data)

# Bij 100,000 analyses:
# → 5-10 seconden query tijd 🐌
```

**Beperkingen:**
```sql
-- SQLite heeft geen:
❌ Parallel queries (1 CPU core)
❌ Partial indexes
❌ Expression indexes
❌ Query planner hints
❌ Table partitioning
❌ Materialized views
```

#### PostgreSQL: Geavanceerd ✅

**Meerdere index types:**
```sql
-- B-tree index (standaard)
CREATE INDEX idx_workplace ON analyses(workplace_id);

-- BRIN index (voor timestamps)
CREATE INDEX idx_timestamp ON analyses USING BRIN(timestamp);

-- Composite index
CREATE INDEX idx_class_conf ON analyses(predicted_class, confidence);

-- Partial index (alleen voor NOK cases)
CREATE INDEX idx_nok ON analyses(confidence)
WHERE predicted_class = 1;

-- Expression index
CREATE INDEX idx_date ON analyses(DATE(timestamp));

-- GIN index voor JSONB
CREATE INDEX idx_metadata ON analyses USING GIN(metadata);
```

**Query optimization:**
```sql
-- PostgreSQL gebruikt ALLE relevante indexen
EXPLAIN ANALYZE
SELECT * FROM analyses
WHERE workplace_id = 1
  AND timestamp > '2025-12-01'
  AND predicted_class = 0
ORDER BY confidence DESC
LIMIT 10;

-- Output:
-- → Bitmap Index Scan (combineert 3 indexen!)
-- → Execution time: 0.5ms ⚡ (100,000 rows)

-- SQLite zelfde query: 5000ms 🐌
```

**Parallel queries:**
```sql
-- PostgreSQL kan queries verdelen over CPU cores
SET max_parallel_workers_per_gather = 4;

-- Heavy aggregation:
SELECT workplace_id,
       COUNT(*),
       AVG(confidence)
FROM analyses
GROUP BY workplace_id;

-- PostgreSQL: 4 cores → 4x sneller
-- SQLite: 1 core → altijd langzaam
```

---

### 📈 7. PRODUCTIE SCENARIO'S

#### Scenario A: Schalen naar 50 Gebruikers

**Met SQLite:**
```
50 operators × 10 inspecties/uur
= 500 writes per uur
= 8-9 writes per minuut

SQLite locking:
┌─────────────────────────────────────┐
│ 90% van de tijd: WACHTEN           │
│ 10% van de tijd: Daadwerkelijk werk│
└─────────────────────────────────────┘

Resultaat:
→ Timeout errors
→ "Database is locked" errors
→ Slechte user experience
```

**Met PostgreSQL:**
```
500 writes per uur → No problem

PostgreSQL handles:
→ 1000+ connections
→ 10,000+ writes per seconde
→ Geen locking issues

Resultaat:
→ Snelle responses
→ Tevreden gebruikers
```

#### Scenario B: 24/7 Beschikbaarheid

**Met SQLite:**
```
Backup:
→ Stop backend ❌
→ Kopieer database
→ Start backend
→ 5-10 minuten downtime

Updates:
→ Stop backend ❌
→ ALTER TABLE
→ Start backend
→ Downtime

Crash:
→ File corruption mogelijk
→ Geen redundancy
→ Data loss risico
```

**Met PostgreSQL:**
```
Backup:
→ pg_dump tijdens productie ✅
→ 0 downtime

Updates:
→ Online schema migrations ✅
→ 0 downtime

High Availability:
Primary ──replication──> Standby
   ↓ (crash)
Standby wordt Primary (30 sec)
→ 99.9% uptime
```

---

## MySQL vs PostgreSQL

### Verschillen

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| **Populariteit** | #1 Web databases | #1 Advanced databases |
| **Snelheid (simpel)** | Iets sneller | Iets langzamer |
| **Snelheid (complex)** | Goed | Excellent |
| **JSON support** | Ja | JSONB (beter) |
| **Full-text search** | Beperkt | Uitgebreid |
| **Window functions** | Ja (8.0+) | Ja (ouder) |
| **Arrays** | Nee | Ja |
| **Data integriteit** | Goed | Strenger |
| **Licentie** | GPL (Oracle) | PostgreSQL (vrij) |
| **Webhosts** | Bijna overal | Minder verspreid |

### MySQL Voordelen

```
✅ Populairder (meer tutorials)
✅ Sneller voor simpele queries
✅ Makkelijker setup
✅ Veel webhosts hebben MySQL standaard
✅ Grote community
```

### PostgreSQL Voordelen

```
✅ Meer features (JSONB, arrays, enums)
✅ Strictere data integriteit
✅ Beter voor complexe queries
✅ Geavanceerde indexing
✅ Volledig open-source (geen Oracle)
✅ Better standards compliance
```

### Voor jouw AI Project

**PostgreSQL aanbevolen omdat:**

```python
# 1. JSONB voor model metadata
model_config = {
    'type': 'classification',
    'classes': ['OK', 'NOK'],
    'threshold': 0.7
}
# PostgreSQL: Native JSONB, snel queryen
# MySQL: JSON support, maar langzamer

# 2. Array types voor detection results
detections = [
    {'class': 'hamer', 'bbox': [10, 20, 50, 60]},
    {'class': 'schaar', 'bbox': [100, 120, 150, 160]}
]
# PostgreSQL: Native arrays
# MySQL: Moet als JSON of aparte tabel

# 3. Full-text search voor notities
"operator melding over ontbrekend gereedschap"
# PostgreSQL: Built-in FTS
# MySQL: Beperktere opties

# 4. Window functions voor analytics
SELECT
    DATE(timestamp),
    AVG(confidence) OVER (
        ORDER BY timestamp
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as rolling_avg
FROM analyses;
# PostgreSQL: Uitstekend
# MySQL: Goed (vanaf 8.0)
```

**Maar MySQL is ook prima als:**
```
✅ Je al MySQL Workbench kent
✅ Je webhost alleen MySQL heeft
✅ Je simpele queries hebt (CRUD)
✅ Je PHP/WordPress achtergrond hebt
```

---

## Management Tools

### Wat zijn Management Tools?

```
Database Management Tool ≠ Database

Vergelijking:
┌─────────────────┬──────────────────┬─────────────────┐
│ Database        │ Management Tool  │ Alternatief     │
├─────────────────┼──────────────────┼─────────────────┤
│ MySQL           │ MySQL Workbench  │ phpMyAdmin      │
│ PostgreSQL      │ pgAdmin          │ DBeaver         │
│ SQLite          │ DB Browser       │ SQLiteStudio    │
└─────────────────┴──────────────────┴─────────────────┘

Net zoals:
VS Code      ≠  Python
(editor)        (taal)

MySQL Workbench  ≠  MySQL
(GUI tool)          (database)
```

### pgAdmin (PostgreSQL)

```
✅ Officiële PostgreSQL GUI
✅ Gratis & open-source
✅ Visuele query builder
✅ Database design tools
✅ ERD (Entity Relationship) diagrams
✅ Cross-platform (Windows/Mac/Linux)
✅ SQL editor met syntax highlighting

Download: https://www.pgadmin.org/
```

**Features:**
- Visual query builder
- Schema browser
- Data import/export
- Backup/restore wizard
- Server monitoring
- Query history

### DBeaver (Universeel) ⭐ AANBEVOLEN

```
✅ Werkt met PostgreSQL, MySQL, SQLite, ALLES!
✅ Moderne interface
✅ Uitstekende gratis versie
✅ SQL formatter & auto-complete
✅ ER diagrams
✅ Data editor
✅ Import/export (CSV, JSON, Excel)
✅ Cross-platform

Download: https://dbeaver.io/
```

**Waarom DBeaver?**
- 1 tool voor alle databases
- Moderne UX (beter dan pgAdmin)
- Goede gratis versie
- Sneller dan pgAdmin
- Betere autocomplete

### MySQL Workbench (MySQL)

```
✅ Officiële MySQL GUI
✅ Database design (forward/reverse engineering)
✅ SQL development
✅ Server administration
✅ Data modeling
✅ Migration tools

Download: https://dev.mysql.com/downloads/workbench/
```

### DB Browser for SQLite

```
✅ Simpele SQLite GUI
✅ Gratis & open-source
✅ Create/edit databases
✅ Execute SQL
✅ Import/export

Download: https://sqlitebrowser.org/
```

---

## Wanneer Welke Database?

### Decision Tree

```
Kies je database:

┌─ Hoeveel gelijktijdige gebruikers? ─┐
│                                       │
│  < 5 users              > 10 users   │
│     ↓                        ↓        │
│  SQLite OK           MySQL/PostgreSQL│
│                                       │
└───────────────────────────────────────┘

┌─ Complexe queries/analytics? ─┐
│                                 │
│  Ja              Nee            │
│   ↓               ↓             │
│ PostgreSQL      MySQL OK        │
│                                 │
└─────────────────────────────────┘

┌─ Cloud deployment? ─┐
│                       │
│  Ja          Nee     │
│   ↓           ↓      │
│ PostgreSQL  SQLite OK│
│ / MySQL              │
│                       │
└───────────────────────┘
```

### SQLite - Perfect Voor

```
✅ Development/Prototyping
   - Snel setup, geen server
   - Perfect voor jouw huidige fase!

✅ Embedded applicaties
   - Mobiele apps
   - Desktop software
   - IoT devices
   - Browser storage

✅ Lage traffic (<10 users)
   - Persoonlijke tools
   - Interne dashboards (kleine teams)
   - Caching layer

✅ Read-heavy workloads
   - Static website content
   - Configuration storage
   - Logs (write once, read many)

✅ Simpele data
   - Geen complexe queries
   - Geen analytics
```

### MySQL - Perfect Voor

```
✅ Web applicaties
   - WordPress, Drupal
   - E-commerce (Magento, WooCommerce)
   - Content Management Systems

✅ LAMP/LEMP stack
   - Linux, Apache/Nginx, MySQL, PHP

✅ Simpele CRUD applicaties
   - User management
   - Blog systems
   - Forums

✅ Gedeelde webhosting
   - Bijna elke webhost heeft MySQL
   - cPanel/Plesk standaard

✅ PHP projecten
   - Laravel, Symfony
   - Veel PHP libraries voor MySQL
```

### PostgreSQL - Perfect Voor

```
✅ Complexe applicaties
   - Analytics platforms
   - Data warehousing
   - Reporting systems

✅ AI/ML projecten (zoals jouw app!)
   - JSON metadata opslag
   - Array data types
   - Complex queries voor analytics

✅ Financial/Banking
   - Strikte data integriteit
   - ACID compliance
   - Transactie support

✅ Geospatial data
   - PostGIS extensie
   - Maps, locations

✅ Modern web frameworks
   - Django (Python)
   - Ruby on Rails
   - Node.js (Sequelize, TypeORM)

✅ Microservices architectuur
   - Schaalbaar
   - Cloud-native
```

---

## Voor Jouw AI Werkplek Inspectie

### Nu (PoC Fase)

```
✅ Gebruik: SQLite

Redenen:
- Snel ontwikkelen
- Geen server setup nodig
- Weinig gebruikers (<5)
- Focus op features, niet infrastructure

Setup:
DATABASE_URL = "sqlite:///backend/data/analyses.db"
```

### Later (Productie)

#### Migreer naar PostgreSQL als:

```
🔴 MOET migreren:
✅ > 10 gelijktijdige gebruikers
✅ "Database locked" errors
✅ Cloud deployment (meerdere servers)
✅ 24/7 beschikbaarheid vereist

🟡 OVERWEEG migreren:
✅ > 100,000 analyses in database
✅ Complexe queries worden traag
✅ Backup/recovery belangrijk
✅ Audit logging nodig
✅ Team groeit (>5 developers)

Triggers:
- Performance problemen
- Concurrency errors
- Schaalvraag
```

#### MySQL is ook prima als:

```
✅ Je al MySQL Workbench kent/gebruikt
✅ Je webhost heeft MySQL maar geen PostgreSQL
✅ Je simpele queries hebt (CRUD operaties)
✅ Je team PHP/MySQL ervaring heeft
✅ Kosten belangrijk (MySQL vaak goedkoper op webhosts)
```

---

## Migratie Strategie

### Voorbereiding (Doe NU!)

**Gebruik SQLAlchemy ORM:**

```python
# ❌ FOUT: Directe SQL (moeilijk te migreren)
import sqlite3
conn = sqlite3.connect('analyses.db')
cursor = conn.cursor()
cursor.execute("INSERT INTO analyses VALUES (?, ?, ?)", data)
conn.commit()

# ✅ GOED: SQLAlchemy (makkelijk te migreren)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Development (SQLite)
engine = create_engine('sqlite:///analyses.db')

# Productie (PostgreSQL) - later 1 regel wijzigen:
# engine = create_engine('postgresql://user:pass@localhost/refresco')

Session = sessionmaker(bind=engine)
session = Session()

# Al je code blijft werken! ✅
```

**Database models:**

```python
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Analysis(Base):
    __tablename__ = 'analyses'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    workplace_id = Column(Integer)
    predicted_class = Column(Integer)
    confidence = Column(Float)
    image_path = Column(String)

# Werkt met SQLite, MySQL, PostgreSQL! ✅
```

### Migratie Stappen

#### Stap 1: Voorbereiding

```bash
# 1. Test je huidige database
# Run alle queries, check of alles werkt

# 2. Maak backup
cp backend/data/analyses.db backup/analyses_backup.db

# 3. Installeer PostgreSQL
# Windows: Download installer
# Mac: brew install postgresql
# Linux: sudo apt install postgresql
```

#### Stap 2: PostgreSQL Setup

```bash
# Start PostgreSQL
sudo service postgresql start

# Maak database
createdb refresco

# Maak user
createuser -P api_user
# Password: [enter password]

# Geef rechten
psql refresco
GRANT ALL PRIVILEGES ON DATABASE refresco TO api_user;
```

#### Stap 3: Schema Migratie

```python
# update_database.py
from sqlalchemy import create_engine
from models import Base  # Je SQLAlchemy models

# Maak schema in PostgreSQL
engine = create_engine('postgresql://api_user:pass@localhost/refresco')
Base.metadata.create_all(engine)

print("Schema created!")
```

#### Stap 4: Data Migratie

**Optie A: pgloader (automatisch)**
```bash
# Installeer pgloader
# Ubuntu: sudo apt install pgloader
# Mac: brew install pgloader

# Run migratie
pgloader sqlite://backend/data/analyses.db \
         postgresql://api_user:pass@localhost/refresco

# Klaar! Data is gemigreerd
```

**Optie B: Export/Import (handmatig)**
```bash
# 1. Export SQLite naar SQL
sqlite3 analyses.db .dump > data.sql

# 2. Clean up voor PostgreSQL
# Edit data.sql:
# - Verwijder SQLite specifieke pragmas
# - Fix syntax verschillen

# 3. Import in PostgreSQL
psql refresco < data.sql
```

**Optie C: Python script (meeste controle)**
```python
# migrate.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Analysis, Workplace  # etc.

# Oude database (SQLite)
old_engine = create_engine('sqlite:///analyses.db')
OldSession = sessionmaker(bind=old_engine)
old_session = OldSession()

# Nieuwe database (PostgreSQL)
new_engine = create_engine('postgresql://api_user:pass@localhost/refresco')
NewSession = sessionmaker(bind=new_engine)
new_session = NewSession()

# Migreer analyses
analyses = old_session.query(Analysis).all()
for analysis in analyses:
    new_session.add(analysis)

new_session.commit()
print(f"Migrated {len(analyses)} analyses")

# Herhaal voor alle tabellen
```

#### Stap 5: Update Applicatie

```python
# backend/config.py

import os
from sqlalchemy import create_engine

# Environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///backend/data/analyses.db'  # Default
)

engine = create_engine(DATABASE_URL)

# Nu switch met environment variable:
# Development: (niet instellen, gebruikt SQLite)
# Production: export DATABASE_URL="postgresql://..."
```

#### Stap 6: Testen

```bash
# 1. Start backend met PostgreSQL
export DATABASE_URL="postgresql://api_user:pass@localhost/refresco"
python backend/main.py

# 2. Test alle functionaliteit
# - Inspectie maken
# - Analyses ophalen
# - Training data exporteren
# - Model uploaden

# 3. Performance test
# - 10 gelijktijdige requests
# - Check response times
```

#### Stap 7: Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: refresco
      POSTGRES_USER: api_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://api_user:secure_password@database:5432/refresco
    depends_on:
      - database
    ports:
      - "8000:8000"

volumes:
  postgres_data:
```

---

## 💰 Kosten Vergelijking

### SQLite
```
Database software: GRATIS
Server: €0 (embedded)
Managed hosting: n.v.t.
Backup: Kopieer bestand (gratis)
Monitoring: n.v.t.

Totaal: €0/maand
```

### PostgreSQL (Self-hosted)
```
Database software: GRATIS (open-source)
Server (VPS): €5-20/maand
  - DigitalOcean Droplet: €6/maand
  - Linode: €5/maand
  - AWS EC2 t3.micro: €8/maand
Backup storage: €2-5/maand
Monitoring: Gratis (open-source tools)

Totaal: €7-25/maand
```

### PostgreSQL (Managed)
```
Azure Database for PostgreSQL:
  - Basic (1 vCore): €25/maand
  - Standard (2 vCore): €100/maand
  - Premium: €500+/maand

AWS RDS PostgreSQL:
  - db.t3.micro: €15/maand
  - db.t3.small: €30/maand
  - db.m5.large: €150/maand

Google Cloud SQL:
  - db-f1-micro: €10/maand
  - db-n1-standard-1: €50/maand

Totaal: €10-500+/maand (afhankelijk van grootte)
```

### MySQL
```
Vergelijkbaar met PostgreSQL:
Self-hosted: €5-25/maand
Managed: €10-500/maand

Voordeel MySQL:
- Vaak goedkoper/gratis bij webhosts
- Shared hosting: €3-10/maand (inclusief MySQL)
```

---

## 📊 Beslismatrix

| Criterium | SQLite | MySQL | PostgreSQL |
|-----------|--------|-------|------------|
| **Setup tijd** | 0 min | 30 min | 30 min |
| **Kosten** | €0 | €5-30 | €7-30 |
| **Concurrent users** | < 5 | 100+ | 1000+ |
| **Data integriteit** | Matig | Goed | Excellent |
| **JSON support** | Basic | Ja | JSONB (best) |
| **Arrays** | Nee | Nee | Ja |
| **Full-text search** | Basic | Ja | Excellent |
| **GIS support** | Nee | Beperkt | PostGIS (best) |
| **Backup tijdens gebruik** | Risico | Veilig | Veilig |
| **Point-in-time recovery** | Nee | Ja | Ja |
| **High availability** | Nee | Ja | Ja |
| **Community support** | Groot | Zeer groot | Groot |
| **Enterprise support** | Nee | Ja (Oracle) | Ja |
| **Learning curve** | Laag | Medium | Medium |

---

## ✅ Samenvatting & Aanbeveling

### Quick Reference

**SQLite = Development & Prototypes**
```
✅ Perfect voor PoC
✅ Geen setup nodig
✅ Snel ontwikkelen
❌ Niet schaalbaar
❌ Geen concurrent writes
```

**MySQL = Web Applications**
```
✅ Populair voor web
✅ Veel hosting support
✅ Grote community
⚠️ Minder features dan PostgreSQL
```

**PostgreSQL = Enterprise & Complex Apps**
```
✅ Meeste features
✅ Best voor AI/ML projecten
✅ Excellent performance
✅ Strikte data integriteit
⚠️ Iets complexere setup
```

### Voor Jouw AI Werkplek Inspectie

**Roadmap:**

```
Fase 1 (Nu): SQLite
├─ Development & PoC
├─ 1-5 gebruikers
└─ Focus op features

Fase 2 (3-6 maanden): PostgreSQL
├─ 10+ gebruikers
├─ Cloud deployment
└─ Production-ready

Fase 3 (1+ jaar): PostgreSQL + Scaling
├─ High availability
├─ Replication
└─ Advanced features
```

**Acties:**

```
✅ NU:
1. Blijf bij SQLite voor development
2. Implementeer SQLAlchemy ORM
3. Write database-agnostic code

✅ BINNENKORT:
1. Monitor performance/concurrency
2. Plan PostgreSQL migratie
3. Setup staging environment

✅ LATER:
1. Migreer naar PostgreSQL
2. Setup backups & monitoring
3. Implement high availability
```

---

**Laatste update:** 29 December 2025
**Voor vragen:** Zie je development team of database administrator
