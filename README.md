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
```text
job-application-tracker/
│
├── app.py                  # Flask routes: pages, CRUD, filters, Job Match
├── database.py             # MySQL connection and query helpers
├── translations.py         # Spanish interface translations
├── schema.sql              # Creates database, tables, and sample data
├── requirements.txt        # Python dependencies
├── README.md
├── AI_USAGE.md             # GenAI usage documentation
│
├── static/
│   └── style.css           # Light and dark themes
│
└── templates/
    ├── base.html
    ├── _filters.html
    ├── dashboard.html
    ├── companies.html
    ├── company_form.html
    ├── company_detail.html
    ├── jobs.html
    ├── job_form.html
    ├── applications.html
    ├── application_form.html
    ├── contacts.html
    ├── contact_form.html
    ├── job_match.html
    └── not_found.html
```

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

MySQL 8.0.16 or newer

Git

MySQL Workbench (optional, but recommended)

2. Clone the repository

```python
git clone https://github.com/ArmandoJA/job-application-tracker.git
cd job-application-tracker
```

3. Configure MySQL

Important: This project uses MySQL port 3307 by default to keep it separate from other MySQL installations or databases running on port 3306.

The schema.sql script starts with DROP DATABASE IF EXISTS job_tracker;. It deletes and recreates the job_tracker database on whichever MySQL server you connect to.

Make sure you connect to the correct MySQL server on port 3307 before running the script. Do not use port 3306 if it contains databases you want to keep.

Using MySQL Workbench

Open MySQL Workbench.

Create or select a connection to your MySQL Server running on port 3307.

Open the schema.sql file from the cloned project.

Before executing the script, verify your connection by running:
```python
SELECT @@port;
```

Confirm the result is 3307.

Execute the entire schema.sql script using the lightning bolt button.

Using the command line

On Windows PowerShell, run:
```python
mysql -h 127.0.0.1 -P 3307 -u root -p < schema.sql
```
Enter your MySQL password when prompted.

If your MySQL username is different from root, replace it with your username.

After running the script, verify the tables were created:
```python
USE job_tracker;
SHOW TABLES;
```
You should see four tables: applications, companies, contacts, and jobs.

4. Install Python dependencies

Create a virtual environment:

# Windows (PowerShell):
```python
python -m venv venv
```
Activate it:
```python
.\venv\Scripts\Activate.ps1
```
If PowerShell says script execution is disabled, run this in the same terminal and activate again:
```python
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
Install dependencies:
```python
pip install -r requirements.txt
```
# macOS / Linux:
```python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
5. Configure the database connection

The application reads its MySQL connection settings from environment variables.

Variable | Default | Description
===========================================
DB_HOST  | 127.0.0.1 | MySQL server address
===========================================
DB_PORT | 3307 | MySQL server port
===========================================
DB_USER | root | MySQL username
===========================================
DB_PASSWORD | Empty | MySQL password
===========================================
DB_NAME | job_tracker | Database name
===========================================

# Windows (PowerShell):
```python
$env:DB_HOST = "127.0.0.1"

$env:DB_PORT = "3307"

$env:DB_USER = "root"

$env:DB_PASSWORD = "your_mysql_password"

$env:DB_NAME = "job_tracker"
```
Replace your_mysql_password with your actual MySQL password.

If your MySQL Server uses port 3306 instead, change DB_PORT to 3306 only if you intend to use that server and have confirmed it is safe to run the database script there.


# Windows (Command Prompt):
```python
set DB_HOST=127.0.0.1

set DB_PORT=3307

set DB_USER=root

set DB_PASSWORD=your_mysql_password

set DB_NAME=job_tracker
```

# macOS / Linux:
```python
export DB_HOST=127.0.0.1

export DB_PORT=3307

export DB_USER=root

export DB_PASSWORD=your_mysql_password

export DB_NAME=job_tracker
```
Set these variables in the same terminal window used to start the application.

6. Run the application

Make sure your MySQL Server on port 3307 is running and your virtual environment is activated.

Run:
```python
python app.py
```
Open the application in your browser:

http://127.0.0.1:5000

Press Ctrl+C in the terminal to stop the application.

# Using the app
Add data: use the Add button on the Companies, Jobs, Applications and Contacts pages. A job needs a company, and an application needs a job.
Filter: choose your filters and press Apply. Clear resets the page. The Jobs chart and the Applications status bars always describe all of your data, not only the filtered rows.
Date filters: Last 24 hours, Last week and Last month compare against the date posted (jobs) or date applied (applications). These columns store a day, not a time, so "last 24 hours" means yesterday and today. The sample data is dated January 2025 and September 2026, so add a new job or application dated today to see these filters return something.
Salary filter: a job matches when the top of its salary range reaches the amount you pick.
Job Match: type skills separated by commas, for example Python, SQL, Flask. Matching ignores capital letters and extra spaces. Jobs are ranked by the percentage of their required skills you have, and jobs with no requirements listed are not ranked. Add skills to a job in the Requirements box of the job form.
Language and theme: use the EN / ES buttons and the Dark mode button in the top bar. Both remember your choice.
