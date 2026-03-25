-- ============================================================
--  Sample Dataset for Crime Record Management System
-- ============================================================

PRAGMA foreign_keys = ON;

-- Admin user  (password: admin123)
-- Officer user (password: officer123)
INSERT OR IGNORE INTO users (username, password_hash, role) VALUES
    ('admin',   'pbkdf2:sha256:600000$salt$hashadmin',   'admin'),
    ('officer1','pbkdf2:sha256:600000$salt$hashofficer', 'officer');

-- Police Officers
INSERT OR IGNORE INTO police_officer (name, rank, station, badge_no, phone) VALUES
    ('Rajesh Kumar',   'Inspector',        'Central Police Station', 'B-1001', '9876543210'),
    ('Priya Sharma',   'Sub-Inspector',    'East Police Station',    'B-1002', '9876543211'),
    ('Amit Singh',     'Constable',        'West Police Station',    'B-1003', '9876543212'),
    ('Sunita Patel',   'Senior Inspector', 'North Police Station',   'B-1004', '9876543213'),
    ('Ravi Mehta',     'Inspector',        'South Police Station',   'B-1005', '9876543214');

-- Criminals
INSERT OR IGNORE INTO criminal (name, age, gender, address, previous_cases) VALUES
    ('Vikram Rao',     35, 'Male',   '12, MG Road, Delhi',           3),
    ('Sundar Lal',     42, 'Male',   '45, Nehru Nagar, Mumbai',      5),
    ('Kavya Nair',     28, 'Female', '78, Gandhi Street, Chennai',   1),
    ('Mohan Das',      50, 'Male',   '99, Rajpath, Kolkata',         0),
    ('Rekha Verma',    31, 'Female', '23, Ashok Road, Hyderabad',    2),
    ('Sanjay Gupta',   39, 'Male',   '67, Civil Lines, Pune',        4),
    ('Deepak Tiwari',  25, 'Male',   '11, Ring Road, Bangalore',     1),
    ('Meena Kumari',   44, 'Female', '88, Sadar Bazaar, Jaipur',     0);

-- FIRs
INSERT OR IGNORE INTO fir (crime_type, date_filed, location, description, criminal_id, officer_id, status) VALUES
    ('Robbery',     '2025-12-01', 'MG Road, Delhi',           'Armed robbery at jewellery store.',     1, 1, 'Under Investigation'),
    ('Murder',      '2025-12-05', 'Nehru Nagar, Mumbai',      'Homicide case near railway station.',   2, 4, 'Open'),
    ('Fraud',       '2025-12-10', 'Gandhi Street, Chennai',   'Online fraud involving bank accounts.', 3, 2, 'Under Investigation'),
    ('Theft',       '2026-01-03', 'Rajpath, Kolkata',         'Vehicle theft reported.',               4, 3, 'Closed'),
    ('Drug Peddling','2026-01-07','Ashok Road, Hyderabad',    'Drug trafficking network discovered.',  5, 5, 'Open'),
    ('Assault',     '2026-01-15', 'Civil Lines, Pune',        'Physical assault in public place.',     6, 1, 'Open'),
    ('Robbery',     '2026-01-20', 'Ring Road, Bangalore',     'Bike-borne robbers snatched mobile.',   7, 2, 'Under Investigation'),
    ('Forgery',     '2026-02-01', 'Sadar Bazaar, Jaipur',     'Fake documents used for land grab.',    8, 3, 'Closed'),
    ('Murder',      '2026-02-10', 'Civil Lines, Pune',        'Second murder case linked to suspect.', 6, 4, 'Open'),
    ('Fraud',       '2026-02-14', 'MG Road, Delhi',           'Investment fraud scheme.',               1, 2, 'Under Investigation');

-- Case Status
INSERT OR IGNORE INTO case_status (fir_id, investigation_stage, court_status, notes) VALUES
    (1,  'Suspect Interrogation', 'Trial Ongoing',   'Suspect identified; trial in progress.'),
    (2,  'Evidence Collection',   'Pending',         'Forensic evidence being gathered.'),
    (3,  'Charge Sheet Filed',    'Trial Ongoing',   'Charge sheet submitted to court.'),
    (4,  'Completed',             'Convicted',       'Accused convicted; sentenced to 2 years.'),
    (5,  'Initial Inquiry',       'Pending',         'Initial investigation underway.'),
    (6,  'Evidence Collection',   'Pending',         'CCTV footage under analysis.'),
    (7,  'Suspect Interrogation', 'Pending',         'Suspect in custody for questioning.'),
    (8,  'Completed',             'Convicted',       'Case closed with conviction.'),
    (9,  'Initial Inquiry',       'Pending',         'Witnesses being interviewed.'),
    (10, 'Charge Sheet Filed',    'Trial Ongoing',   'Second fraud charge linked to FIR 1.');

-- Audit Log sample entries
INSERT OR IGNORE INTO audit_log (table_name, operation, record_id, changed_by, details) VALUES
    ('criminal',      'INSERT', 1, 'admin', 'Added criminal: Vikram Rao'),
    ('fir',           'INSERT', 1, 'admin', 'Registered FIR #1 for Robbery'),
    ('case_status',   'UPDATE', 1, 'officer1', 'Stage updated to Suspect Interrogation'),
    ('police_officer','INSERT', 1, 'admin', 'Added officer: Rajesh Kumar');
