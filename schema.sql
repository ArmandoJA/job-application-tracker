-- Job Application Tracker schema (MySQL 8+)
DROP DATABASE IF EXISTS job_tracker;
CREATE DATABASE job_tracker;
USE job_tracker;

CREATE TABLE companies (
    company_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_name VARCHAR(100) NOT NULL,
    industry     VARCHAR(50),
    website      VARCHAR(200),
    city         VARCHAR(50),
    state        VARCHAR(50),
    notes        TEXT
);

CREATE TABLE jobs (
    job_id       INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    job_title    VARCHAR(100) NOT NULL,
    job_type     ENUM('Full-time','Part-time','Contract','Internship'),
    salary_min   INT,
    salary_max   INT,
    job_url      VARCHAR(300),
    date_posted  DATE,
    requirements JSON,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE,
    CHECK (salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max)
);

CREATE TABLE applications (
    application_id    INT PRIMARY KEY AUTO_INCREMENT,
    job_id            INT NOT NULL,
    application_date  DATE NOT NULL,
    status            ENUM('Applied','Screening','Interview','Offer','Rejected','Withdrawn')
                      DEFAULT 'Applied',
    resume_version    VARCHAR(50),
    cover_letter_sent BOOLEAN DEFAULT FALSE,
    interview_data    JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        ON DELETE CASCADE
);

CREATE TABLE contacts (
    contact_id   INT PRIMARY KEY AUTO_INCREMENT,
    company_id   INT NOT NULL,
    contact_name VARCHAR(100) NOT NULL,
    title        VARCHAR(100),
    email        VARCHAR(100),
    phone        VARCHAR(20),
    linkedin_url VARCHAR(200),
    notes        TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
);

-- ---------- Sample data ----------
-- Converted from the class job_tracker database (all fictional).
-- Changes made while converting:
--   * contacts: first_name + last_name became contact_name; job_title became title
--   * websites got https:// in front so they pass the app's validation
--   * application statuses mapped to the project's list:
--       'Offer Accepted' -> Offer, 'Interview Completed' -> Interview, 'Phone Screen' -> Screening
--   * requirements is now a JSON array of skills (what Job Match reads). Jobs 1 and 3 use the
--     required_skills from the class data; the other jobs' skill lists were added for the demo.

INSERT INTO companies (company_id, company_name, industry, website, city, state, notes) VALUES
(1, 'Tech Solutions Inc',   'Technology',      'https://www.techsolutions.com',     'Miami',         'Florida',       NULL),
(2, 'Data Analytics Corp',  'Data Science',    'https://www.dataanalytics.com',     'Austin',        'Texas',         NULL),
(3, 'Cloud Systems LLC',    'Cloud Computing', 'https://www.cloudsystems.com',      'Seattle',       'Washington',    NULL),
(4, 'Digital Innovations',  'Software',        'https://www.digitalinnovations.com','San Francisco', 'California',    'Applied to Senior Developer position on 2026-09-28'),
(5, 'Smart Tech Group',     'AI/ML',           'https://www.smarttech.com',         'Boston',        'Massachusetts', NULL),
(7, 'New Tech Corp',        'Technology',      NULL,                                'Denver',        'Colorado',      NULL);

INSERT INTO jobs (job_id, company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1,  1, 'Software Developer',     'Full-time',  70000,  90000,  NULL, '2025-01-15', JSON_ARRAY('Python', 'SQL', 'Git')),
(2,  1, 'Database Administrator', 'Full-time',  75000,  95000,  NULL, '2025-01-10', JSON_ARRAY('SQL', 'MySQL', 'Linux', 'Database Tuning')),
(3,  2, 'Data Analyst',           'Full-time',  65000,  85000,  NULL, '2025-01-12', JSON_ARRAY('SQL', 'Excel', 'Tableau')),
(4,  3, 'Cloud Engineer',         'Full-time',  80000, 100000,  NULL, '2025-01-08', JSON_ARRAY('AWS', 'Linux', 'Docker', 'Python')),
(5,  4, 'Junior Developer',       'Full-time',  55000,  70000,  NULL, '2025-01-14', JSON_ARRAY('Python', 'Git', 'HTML', 'SQL')),
(6,  4, 'Senior Developer',       'Full-time',  95000, 120000,  NULL, '2025-01-14', JSON_ARRAY('Python', 'SQL', 'Flask', 'Docker', 'AWS', 'Git')),
(7,  5, 'ML Engineer',            'Full-time',  90000, 115000,  NULL, '2025-01-11', JSON_ARRAY('Python', 'TensorFlow', 'SQL', 'Statistics')),
(28, 1, 'QA Engineer',            'Full-time',  60000,  80000,  NULL, '2025-01-05', JSON_ARRAY('Python', 'Selenium', 'SQL', 'Test Automation')),
(29, 2, 'Business Analyst',       'Full-time',  65000,  85000,  NULL, '2025-01-06', JSON_ARRAY('SQL', 'Excel', 'Tableau', 'Communication')),
(30, 2, 'Data Scientist',         'Full-time',  85000, 110000,  NULL, '2025-01-07', JSON_ARRAY('Python', 'R', 'SQL', 'Statistics', 'Machine Learning')),
(31, 3, 'DevOps Engineer',        'Full-time',  80000, 105000,  NULL, '2025-01-08', JSON_ARRAY('Docker', 'Linux', 'AWS', 'Git', 'CI/CD')),
(32, 3, 'Security Analyst',       'Full-time',  75000,  95000,  NULL, '2025-01-09', JSON_ARRAY('Python', 'Networking', 'Linux', 'SIEM')),
(33, 4, 'UI/UX Designer',         'Full-time',  60000,  80000,  NULL, '2025-01-10', JSON_ARRAY('Figma', 'HTML', 'CSS', 'User Research')),
(34, 5, 'Product Manager',        'Full-time',  90000, 120000,  NULL, '2025-01-11', JSON_ARRAY('Communication', 'Agile', 'SQL', 'Roadmapping')),
(35, 1, 'Technical Writer',       'Contract',   55000,  75000,  NULL, '2025-01-12', JSON_ARRAY('Technical Writing', 'Git', 'Markdown', 'Communication')),
(36, 2, 'Intern - Data',          'Internship', 30000,  40000,  NULL, '2025-01-13', JSON_ARRAY('Python', 'SQL', 'Excel')),
(37, 4, 'Intern - Development',   'Internship', 32000,  42000,  NULL, '2025-01-14', JSON_ARRAY('Python', 'Git', 'HTML')),
(38, 7, 'Software Architect',     'Full-time', 120000, 150000,  NULL, NULL,         JSON_ARRAY('Python', 'AWS', 'System Design', 'Docker', 'SQL'));

INSERT INTO applications (application_id, job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, 1, '2025-01-16', 'Offer',     'v2.1', TRUE,  NULL),
(2, 3, '2025-01-13', 'Interview', 'v2.1', TRUE,
    '{"round": 2, "interviewer": "Sarah Johnson, Mike Chen, David Brown", "notes": "Strong technical skills, good communication", "feedback": "Strong technical skills, good communication", "next_steps": "Offer extended!", "interviewers": ["Sarah Johnson", "Mike Chen", "David Brown"], "offer_amount": 85000, "interview_rounds": 2, "technical_questions": ["SQL joins", "Python basics", "API design"]}'),
(3, 4, '2025-01-09', 'Interview', 'v2.0', FALSE, NULL),
(4, 5, '2025-01-15', 'Applied',   'v2.1', TRUE,  NULL),
(5, 7, '2025-01-12', 'Screening', 'v2.1', TRUE,
    '{"round": 1, "interviewer": "Emily Williams", "notes": "Needs more experience with cloud platforms", "feedback": "Needs more experience with cloud platforms", "interviewers": ["Emily Williams"], "interview_rounds": 1, "technical_questions": ["Database normalization", "Transaction isolation"]}'),
(6, 6, '2026-09-28', 'Applied',   'v3.0', TRUE,  NULL);

INSERT INTO contacts (contact_id, company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 1, 'Sarah Johnson',  'HR Manager',          'sjohnson@techsolutions.com',      NULL, NULL, NULL),
(2, 2, 'Michael Chen',   'Technical Recruiter', 'mchen@dataanalytics.com',         NULL, NULL, NULL),
(3, 3, 'Emily Williams', 'Hiring Manager',      'ewilliams@cloudsystems.com',      NULL, NULL, NULL),
(4, 4, 'David Brown',    'Senior Developer',    NULL,                              NULL, NULL, NULL),
(5, 5, 'Lisa Garcia',    'Talent Acquisition',  'lgarcia@smarttech.com',           NULL, NULL, NULL),
(7, 4, 'Robert Kim',     'Engineering Manager', 'rkim@digitalinnovations.com',     NULL, NULL, NULL);
