# job-application-tracker
A web application to track job applications - COP 4751 Course Project

# Features
Page	What it does
Dashboard	Applications by status and your most recent applications
Companies	List of companies with the roles you applied to, a detail page for each, and add / edit / delete
Jobs	Donut chart of jobs by type (full-time, part-time, contract, internship), job counts per industry, and add / edit / delete
Applications	Bars showing how many applications are in each status, the list of applications, and add / edit / delete, including optional interview details
Contacts	People you know at the companies you track, with add / edit / delete
Job Match	Enter your skills and see the jobs ranked by match percentage, with the skills you match and the skills you are missing

Also included:

Search and filters on every list page
Companies: search, location, industry
Jobs: search, company, type, salary, date posted
Applications: search, company, date applied, status
Contacts: search
Validation on every form (required fields, lengths, URL and email formats, salary ranges, dates)
Delete confirmations, which also say what else will be deleted (for example, deleting a company removes its jobs, applications and contacts)
English / Spanish switch in the top bar. Only the interface is translated. Company names, job titles, skills and anything you type stay as entered.
Dark mode button. It starts in dark mode when your system or browser is set to dark.

# Tech stack
Python 3.9 or newer
Flask 3
MySQL 8.0.16 or newer (needed for the JSON columns and CHECK constraint)
mysql-connector-python
Bootstrap 5 and Chart.js, loaded from a CDN (an internet connection is needed to see the styling and the chart)

# Project structure
job_tracker/
├── app.py              # Flask routes: pages, CRUD, filters, Job Match
├── database.py         # MySQL connection and query helpers
├── translations.py     # Spanish text for the interface
├── schema.sql          # Creates the database, tables and sample data
├── requirements.txt    # Python dependencies
├── README.md
├── AI_USAGE.md         # How GenAI tools were used
├── static/
│   └── style.css       # Light and dark themes
└── templates/
    ├── base.html       # Top bar, language and dark mode buttons
    ├── _filters.html   # Shared search and filter pieces
    ├── dashboard.html
    ├── companies.html, company_form.html, company_detail.html
    ├── jobs.html, job_form.html
    ├── applications.html, application_form.html
    ├── contacts.html, contact_form.html
    ├── job_match.html
    └── not_found.html

# Database

Four tables, created by schema.sql:

companies (company_id, company_name, industry, website, city, state, notes)
jobs (job_id, company_id → companies, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements JSON)
applications (application_id, job_id → jobs, application_date, status, resume_version, cover_letter_sent, interview_data JSON)
contacts (contact_id, company_id → companies, contact_name, title, email, phone, linkedin_url, notes)

# Details:

Foreign keys use ON DELETE CASCADE: deleting a company deletes its jobs and contacts, and deleting a job deletes its applications.
jobs.requirements holds a JSON array of skills, such as ["Python", "SQL", "Git"]. Job Match reads this column.
applications.interview_data holds a JSON object with interview details (round, type, interviewer, date, notes).
job_type and status are ENUM columns. Status values are Applied, Screening, Interview, Offer, Rejected and Withdrawn.
The script includes fictional sample data so the app has something to show right away.

# Setup
1. Requirements
Python 3.9 or newer
MySQL 8.0.16 or newer, running on your machine (MySQL Workbench is optional but handy)
2. Get the code
bash
git clone <repository-url>
cd job_tracker
3. Create the database

Warning: schema.sql starts with DROP DATABASE IF EXISTS job_tracker;, so it replaces any existing database with that name. Run it on a server where that is fine.

Either open schema.sql in MySQL Workbench and run the whole script (the lightning bolt button), or from a terminal:

bash
mysql -u root -p < schema.sql

You can check it worked with:

sql
USE job_tracker;
SHOW TABLES;

You should see applications, companies, contacts and jobs.

4. Install the Python packages

Windows (PowerShell):

powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

If PowerShell says running scripts is disabled, run this once in the same window and activate again:

powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

macOS / Linux:

bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
5. Tell the app how to reach MySQL

The app reads its connection settings from environment variables, so no password is stored in the code.

Variable	Meaning	Default
DB_HOST	MySQL host	127.0.0.1
DB_PORT	MySQL port	3307
DB_USER	MySQL user	root
DB_PASSWORD	MySQL password	(empty)
DB_NAME	Database name	job_tracker

The default port is 3307. A standard MySQL installation uses 3306, so most people need to set DB_PORT as shown below, plus DB_PASSWORD if the MySQL user has a password.

Windows (PowerShell):

powershell
$env:DB_PORT = "3306"
$env:DB_PASSWORD = "your_mysql_password"

Windows (Command Prompt):

bat
set DB_PORT=3306
set DB_PASSWORD=your_mysql_password

macOS / Linux:

bash
export DB_PORT=3306
export DB_PASSWORD=your_mysql_password

Set these in the same terminal window you use to start the app.

6. Run the app
bash
python app.py

Open http://127.0.0.1:5000 in your browser. Stop the app with Ctrl+C.

# Using the app
Add data: use the Add button on the Companies, Jobs, Applications and Contacts pages. A job needs a company, and an application needs a job.
Filter: choose your filters and press Apply. Clear resets the page. The Jobs chart and the Applications status bars always describe all of your data, not only the filtered rows.
Date filters: Last 24 hours, Last week and Last month compare against the date posted (jobs) or date applied (applications). These columns store a day, not a time, so "last 24 hours" means yesterday and today. The sample data is dated January 2025 and September 2026, so add a new job or application dated today to see these filters return something.
Salary filter: a job matches when the top of its salary range reaches the amount you pick.
Job Match: type skills separated by commas, for example Python, SQL, Flask. Matching ignores capital letters and extra spaces. Jobs are ranked by the percentage of their required skills you have, and jobs with no requirements listed are not ranked. Add skills to a job in the Requirements box of the job form.
Language and theme: use the EN / ES buttons and the Dark mode button in the top bar. Both remember your choice.
