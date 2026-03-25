-- ============================================================
--  Crime Record Management System — Database Schema (SQLite)
-- ============================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------
-- Users / Admin table (login / role-based access)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'officer' CHECK(role IN ('admin','officer')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------
-- Criminal table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS criminal (
    criminal_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    age            INTEGER NOT NULL CHECK(age > 0 AND age < 120),
    gender         TEXT    NOT NULL CHECK(gender IN ('Male','Female','Other')),
    address        TEXT,
    previous_cases INTEGER NOT NULL DEFAULT 0 CHECK(previous_cases >= 0),
    photo_url      TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_criminal_name ON criminal(name);

-- ----------------------------------------------------------
-- Police Officer table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS police_officer (
    officer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    rank        TEXT NOT NULL,
    station     TEXT NOT NULL,
    badge_no    TEXT UNIQUE,
    phone       TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_officer_station ON police_officer(station);

-- ----------------------------------------------------------
-- FIR (First Information Report) table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fir (
    fir_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    crime_type   TEXT    NOT NULL,
    date_filed   TEXT    NOT NULL DEFAULT (date('now')),
    location     TEXT    NOT NULL,
    description  TEXT,
    criminal_id  INTEGER NOT NULL,
    officer_id   INTEGER NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'Open'
                         CHECK(status IN ('Open','Under Investigation','Closed','Dismissed')),
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (criminal_id) REFERENCES criminal(criminal_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (officer_id)  REFERENCES police_officer(officer_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_fir_status      ON fir(status);
CREATE INDEX IF NOT EXISTS idx_fir_crime_type  ON fir(crime_type);
CREATE INDEX IF NOT EXISTS idx_fir_criminal    ON fir(criminal_id);
CREATE INDEX IF NOT EXISTS idx_fir_officer     ON fir(officer_id);

-- ----------------------------------------------------------
-- Case Status table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS case_status (
    case_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fir_id              INTEGER NOT NULL UNIQUE,
    investigation_stage TEXT    NOT NULL DEFAULT 'Initial Inquiry'
                                CHECK(investigation_stage IN (
                                    'Initial Inquiry','Evidence Collection',
                                    'Suspect Interrogation','Charge Sheet Filed',
                                    'Completed')),
    court_status        TEXT    NOT NULL DEFAULT 'Pending'
                                CHECK(court_status IN (
                                    'Pending','Trial Ongoing','Acquitted',
                                    'Convicted','Case Dismissed')),
    notes               TEXT,
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (fir_id) REFERENCES fir(fir_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_case_fir ON case_status(fir_id);

-- ----------------------------------------------------------
-- Audit Log table
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name  TEXT NOT NULL,
    operation   TEXT NOT NULL CHECK(operation IN ('INSERT','UPDATE','DELETE')),
    record_id   INTEGER NOT NULL,
    changed_by  TEXT,
    changed_at  TEXT NOT NULL DEFAULT (datetime('now')),
    details     TEXT
);

-- ----------------------------------------------------------
-- View: Open Cases with criminal and officer details
-- ----------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_open_cases AS
    SELECT
        f.fir_id,
        f.crime_type,
        f.date_filed,
        f.location,
        f.status AS fir_status,
        c.name   AS criminal_name,
        p.name   AS officer_name,
        p.station,
        cs.investigation_stage,
        cs.court_status
    FROM fir f
    JOIN criminal       c  ON f.criminal_id = c.criminal_id
    JOIN police_officer p  ON f.officer_id  = p.officer_id
    LEFT JOIN case_status cs ON f.fir_id    = cs.fir_id
    WHERE f.status IN ('Open','Under Investigation');

-- ----------------------------------------------------------
-- View: Repeat Offenders (previous_cases > 1)
-- ----------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_repeat_offenders AS
    SELECT
        c.criminal_id,
        c.name,
        c.age,
        c.gender,
        c.previous_cases,
        COUNT(f.fir_id) AS total_firs
    FROM criminal c
    LEFT JOIN fir f ON c.criminal_id = f.criminal_id
    WHERE c.previous_cases > 1
    GROUP BY c.criminal_id;
