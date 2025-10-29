# 🗄️ PostgreSQL Database Migration

## Overview

GrowQR has been migrated from a file-based JSON storage system to a professional PostgreSQL database with full relational integrity, indexes, and migration management.

## 🎯 What Changed

### Before (File-Based)
- JSON files stored in `backend/results/`
- No relationships or constraints
- Manual file management
- No search capabilities
- Timestamp-based IDs (collision risk)

### After (PostgreSQL)
- 7 relational tables with foreign keys
- Full ACID compliance
- Alembic migration management
- UUID-based primary keys
- Indexed queries for performance
- Advanced search capabilities

---

## 📊 Database Schema

```
videos (parent table)
  ├─ id: UUID (primary key)
  ├─ original_filename: string
  ├─ stored_filename: string
  ├─ file_size: integer
  ├─ duration: float
  ├─ status: enum (pending, processing, completed, failed)
  └─ timestamps: uploaded_at, processed_at

analyses (1-to-many with videos)
  ├─ id: UUID (primary key)
  ├─ video_id: UUID (foreign key → videos.id)
  ├─ status: enum (pending, processing, completed, failed)
  ├─ progress: integer (0-100)
  ├─ total_duration: float
  └─ timestamps: started_at, completed_at

emotions (1-to-many with analyses)
  ├─ id: serial (primary key)
  ├─ analysis_id: UUID (foreign key → analyses.id)
  ├─ timestamp: float
  ├─ emotion: enum (neutral, happy, serious, passionate, confident, hopeful)
  └─ confidence: float

gestures (1-to-many with analyses)
  ├─ id: serial (primary key)
  ├─ analysis_id: UUID (foreign key → analyses.id)
  ├─ timestamp: float
  ├─ type: enum (hand_raise, pointing, open_arms, hand_gesture)
  ├─ description: text
  └─ confidence: float

transcripts (1-to-many with analyses)
  ├─ id: serial (primary key)
  ├─ analysis_id: UUID (foreign key → analyses.id)
  ├─ segment_index: integer
  ├─ start_time: float
  ├─ end_time: float
  ├─ text: text
  └─ confidence: float

llm_insights (1-to-1 with analyses)
  ├─ id: UUID (primary key)
  ├─ analysis_id: UUID (foreign key → analyses.id)
  ├─ main_topics: jsonb array
  ├─ rhetorical_techniques: jsonb array
  ├─ persuasive_elements: jsonb array
  ├─ persuasion_score: float (1-10)
  ├─ overall_tone: text
  └─ transcript_summary: text

key_moments (1-to-many with analyses)
  ├─ id: serial (primary key)
  ├─ analysis_id: UUID (foreign key → analyses.id)
  ├─ timestamp: float
  ├─ description: text
  └─ type: enum (emotion, gesture, combined)
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- pip

### 1. Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@14
brew services start postgresql@14
```

**Ubuntu/Debian:**
```bash
sudo apt-get install postgresql-14
sudo systemctl start postgresql
```

### 2. Create Database

```bash
# Create database
psql postgres -c "CREATE DATABASE growqr;"

# Create user
psql postgres -c "CREATE USER growqr_user WITH PASSWORD 'your_password';"

# Grant permissions
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE growqr TO growqr_user;"
psql postgres -c "ALTER DATABASE growqr OWNER TO growqr_user;"
```

### 3. Configure Environment

Create `backend/.env`:
```bash
# Database Configuration
DATABASE_URL=postgresql://growqr_user:your_password@localhost:5432/growqr
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Existing API keys...
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
LLM_PROVIDER=openai
```

### 4. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `sqlalchemy>=2.0.0` - ORM framework
- `psycopg2-binary>=2.9.0` - PostgreSQL driver
- `alembic>=1.13.0` - Database migrations
- `pydantic-settings>=2.0.0` - Settings management

### 5. Run Migrations

```bash
# Apply all migrations (creates tables)
alembic upgrade head
```

---

## 📁 New Project Structure

```
backend/
├── database/                    ← NEW: Database layer
│   ├── __init__.py
│   ├── connection.py           ← Database connection & session management
│   ├── models.py               ← SQLAlchemy ORM models
│   └── crud.py                 ← Database operations (Create, Read, Update, Delete)
│
├── alembic/                     ← NEW: Migration system
│   ├── versions/               ← Migration files (version controlled!)
│   │   └── e4a54530f7ca_initial_migration_create_all_tables.py
│   ├── env.py                  ← Alembic environment config
│   └── README
│
├── alembic.ini                  ← NEW: Alembic configuration
│
├── scripts/                     ← NEW: Helper scripts
│   └── clear_database.py       ← Clear all database data
│
├── processing/                  ← Existing processors (unchanged)
│   ├── video_processor.py
│   ├── audio_processor.py
│   └── llm_analyzer.py
│
├── main.py                      ← Updated to use database
├── requirements.txt             ← Updated with DB dependencies
└── .env                         ← Updated with DATABASE_URL
```

---

## 🔧 Database Management

### Check Database Status
```bash
# List all tables
psql $DATABASE_URL -c "\dt"

# Count records
psql $DATABASE_URL -c "
SELECT
  'videos' as table, COUNT(*) FROM videos
  UNION ALL
  SELECT 'analyses', COUNT(*) FROM analyses
  UNION ALL
  SELECT 'emotions', COUNT(*) FROM emotions;
"
```

### Clear All Data
```bash
# Using helper script (recommended)
python scripts/clear_database.py

# Or direct SQL
psql $DATABASE_URL -c "
TRUNCATE TABLE key_moments, llm_insights, transcripts,
               gestures, emotions, analyses, videos
RESTART IDENTITY CASCADE;
"
```

### Create New Migration
```bash
# After changing models.py
alembic revision --autogenerate -m "Description of changes"

# Apply the migration
alembic upgrade head
```

### Rollback Migration
```bash
# Rollback last migration
alembic downgrade -1

# Rollback all migrations
alembic downgrade base
```

---

## 🔍 Querying the Database

### Using Python CRUD Functions

```python
from database import crud, get_db

db = next(get_db())

# Get all videos
videos = crud.get_all_videos(db, limit=10)

# Get analysis with all data
analysis_data = crud.get_complete_analysis_data(db, analysis_id)

# Search by topic
analyses = crud.search_analyses_by_topic(db, "leadership")

# Find high persuasion scores
top_analyses = crud.get_high_persuasion_analyses(db, min_score=8.0)
```

### Using SQL Directly

```sql
-- Find videos with high persuasion scores
SELECT v.original_filename, l.persuasion_score, l.main_topics
FROM videos v
JOIN analyses a ON a.video_id = v.id
JOIN llm_insights l ON l.analysis_id = a.id
WHERE l.persuasion_score >= 8.0
ORDER BY l.persuasion_score DESC;

-- Get emotion timeline for a video
SELECT timestamp, emotion, confidence
FROM emotions
WHERE analysis_id = 'uuid-here'
ORDER BY timestamp;

-- Search transcripts
SELECT v.original_filename, t.text
FROM transcripts t
JOIN analyses a ON a.id = t.analysis_id
JOIN videos v ON v.id = a.video_id
WHERE t.text ILIKE '%motivation%';
```

---

## 🛠️ Troubleshooting

### Connection Issues

**Error:** `could not connect to server`
```bash
# Check PostgreSQL is running
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Start if needed
brew services start postgresql@14
```

**Error:** `FATAL: password authentication failed`
```bash
# Verify credentials in .env
echo $DATABASE_URL

# Reset user password
psql postgres -c "ALTER USER growqr_user WITH PASSWORD 'new_password';"
```

### Migration Issues

**Error:** `Target database is not up to date`
```bash
# Check current version
alembic current

# Apply pending migrations
alembic upgrade head
```

**Error:** `Can't locate revision identified by 'xyz'`
```bash
# Clear alembic version table
psql $DATABASE_URL -c "DELETE FROM alembic_version;"

# Stamp current version
alembic stamp head
```

---

## 📈 Performance Considerations

### Indexes Created
- Primary key indexes on all tables
- Foreign key indexes for relationships
- Timestamp indexes for time-based queries
- Emotion/gesture type indexes for filtering

### Connection Pooling
- Pool size: 5 connections
- Max overflow: 10 connections
- Pre-ping enabled (validates connections)

### Query Optimization
- Use `get_complete_analysis_data()` for full data retrieval
- Leverage indexes for timestamp-based queries
- JSONB columns for flexible array storage

---

## 🔒 Security

### What's Protected
- ✅ `.env` file ignored by git (credentials safe)
- ✅ Parameterized queries (SQL injection protection)
- ✅ Foreign key constraints (data integrity)
- ✅ User-specific database credentials

### Best Practices
- 🔐 Never commit `.env` file
- 🔐 Use strong passwords for production
- 🔐 Enable SSL for production databases
- 🔐 Regularly backup database
- 🔐 Limit database user permissions

---

## 🚢 Production Deployment

### Environment Variables
Set these in your production environment:
```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### Migration on Deploy
```bash
# Include in deploy script
alembic upgrade head
```

### Backup Strategy
```bash
# Daily backups
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore if needed
psql $DATABASE_URL < backup_20251029.sql
```

---

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)

---

## ✅ Migration Checklist

- [x] PostgreSQL installed and running
- [x] Database and user created
- [x] Environment variables configured
- [x] Dependencies installed
- [x] Migrations run successfully
- [x] Tables created with proper schema
- [x] Foreign keys and indexes in place
- [x] CRUD operations tested
- [x] API endpoints updated
- [x] Frontend hydration fixed
- [x] Video path URLs corrected
- [x] Performance optimized (throttling)

---

**Migration completed on:** October 29, 2025
**Database version:** Initial migration (e4a54530f7ca)
