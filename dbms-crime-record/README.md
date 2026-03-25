# 🛡️ Crime Record Management System (CRMS)

A full-stack, database-driven web application for police departments to digitally manage crime records, FIRs, officer assignments, and case investigation status.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Run the Application

**Option 1 — Double-click `run.bat`**

**Option 2 — Terminal**
```bash
pip install Flask Werkzeug
python app.py
```

Open your browser at → **http://127.0.0.1:5000**

---

## 🔐 Demo Credentials

| Role    | Username  | Password    |
|---------|-----------|-------------|
| Admin   | `admin`   | `admin123`  |
| Officer | `officer1`| `officer123`|

---

## 🏗 Project Structure

```
dbms-crime-record/
├── app.py              # Flask backend — all routes & business logic
├── schema.sql          # Database schema (tables, views, indexes)
├── sample_data.sql     # Pre-loaded sample dataset
├── requirements.txt    # Python dependencies
├── run.bat             # Windows quick-start script
├── static/
│   ├── css/style.css   # Custom dark theme styles
│   └── js/main.js      # Charts, clock, confirm-delete
└── templates/
    ├── base.html       # Sidebar layout
    ├── login.html      # Login page
    ├── dashboard.html  # Dashboard with charts
    ├── criminals/      # Criminal CRUD pages
    ├── fir/            # FIR CRUD pages
    ├── officers/       # Officer CRUD pages
    ├── cases/          # Case status tracking
    └── reports/        # Reports & analytics
```

---

## 🗂 Database Schema

### Tables

| Table            | Primary Key   | Description                          |
|------------------|---------------|--------------------------------------|
| `users`          | `user_id`     | Admin & officer login accounts       |
| `criminal`       | `criminal_id` | Criminal personal details            |
| `police_officer` | `officer_id`  | Officer profiles                     |
| `fir`            | `fir_id`      | FIR records (links criminal+officer) |
| `case_status`    | `case_id`     | Investigation & court tracking       |
| `audit_log`      | `log_id`      | Change history of all records        |

### Views
- `v_open_cases` — Open + Under Investigation FIRs with full details
- `v_repeat_offenders` — Criminals with `previous_cases > 1`

### Relationships
```
criminal (1) ──── (M) fir
police_officer (1) ── (M) fir
fir (1) ──────────── (1) case_status
```

---

## ⚙ Features

### ✅ Criminal Management
- Add, view, edit, delete criminal profiles
- Tracks previous case count
- Highlights repeat offenders

### ✅ FIR Management
- Register new FIRs with crime type, location, description
- Link to criminal and investigating officer
- Auto-increments criminal's case count on new FIR
- Filter by status or crime type

### ✅ Officer Management
- Full officer directory with rank, station, badge, phone
- View all FIRs assigned to each officer

### ✅ Case Tracking
- Update investigation stage (5 stages)
- Track court status (5 outcomes)
- Auto-syncs FIR status based on case progress

### ✅ Reports & Analytics
- Crime type distribution table + bar charts
- Open/active cases report
- Repeat offenders report
- FIRs handled per officer
- Audit log of all database changes

### ✅ Dashboard
- 8 real-time KPI stat cards
- Chart.js bar chart (crime types)
- Chart.js doughnut (FIR status breakdown)
- Recent FIRs table
- Crime frequency bars

### ✅ Security
- Login required on all routes
- Admin-only for add/edit/delete officers and delete criminals/FIRs
- Role-based access (admin / officer)
- Password hashing via Werkzeug PBKDF2

---

## 🔍 Key SQL Queries Used

```sql
-- Open cases
SELECT fir_id, crime_type FROM fir WHERE status = 'Open';

-- Repeat offenders
SELECT name, previous_cases FROM criminal WHERE previous_cases > 2;

-- FIR + Officer JOIN
SELECT F.fir_id, F.crime_type, P.name
FROM fir F JOIN police_officer P ON F.officer_id = P.officer_id;

-- FIRs per officer
SELECT p.name, COUNT(f.fir_id) AS total_firs
FROM police_officer p
LEFT JOIN fir f ON p.officer_id = f.officer_id
GROUP BY p.officer_id;
```

---

## 🎨 UI Design

- **Background:** `#111111`
- **Primary (red):** `#b30000`
- **Accent:** `#ff3333`
- **Text:** `#ffffff`
- **Font:** Rajdhani (headings) + Inter (body)
- **Icons:** Bootstrap Icons CDN
- **Charts:** Chart.js 4

---

## 📊 DBMS Concepts Demonstrated

| Concept             | Implementation                                       |
|---------------------|------------------------------------------------------|
| Relational Design   | 6 normalized tables                                  |
| Primary Keys        | All tables have `INTEGER PRIMARY KEY AUTOINCREMENT`  |
| Foreign Keys        | `fir.criminal_id`, `fir.officer_id`, `case_status.fir_id` |
| Constraints         | `CHECK`, `UNIQUE`, `NOT NULL`, `DEFAULT`             |
| Indexes             | On `name`, `status`, `crime_type`, `station`         |
| Views               | `v_open_cases`, `v_repeat_offenders`                 |
| Joins               | Multi-table JOINs in all list/report queries         |
| Transactions        | SQLite auto-commit via `db.commit()`                 |
| Normalization       | 3NF — no repeating groups, no transitive deps        |
| Audit Log           | Tracks all INSERT/UPDATE/DELETE with user + timestamp|
