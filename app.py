import json
import re
from datetime import datetime, date, timedelta

from flask import (Flask, render_template, request, redirect, url_for, flash, abort,
                   session)

from translations import ES

from database import query, execute

app = Flask(__name__)
app.secret_key = "change-me-before-submitting"  # needed for flash messages


# ------------------------------------------------------------- Language (i18n)
# Only the interface is translated. Company names, job titles, skills, contact
# names and other things you type stay exactly as you entered them.
LANGUAGES = {"en": "English", "es": "Español"}


def current_lang():
    """The saved choice, else the browser's preferred language, else English."""
    lang = session.get("lang")
    if lang in LANGUAGES:
        return lang
    return request.accept_languages.best_match(list(LANGUAGES)) or "en"


def tr(text, **values):
    """Translate an English interface string (English is the key), then fill {placeholders}."""
    out = ES.get(text, text) if current_lang() == "es" else text
    return out.format(**values) if values else out


app.add_template_global(tr, name="_")


@app.context_processor
def inject_language():
    return {"lang": current_lang()}


@app.route("/language", methods=["POST"])
def set_language():
    lang = request.form.get("lang", "")
    if lang in LANGUAGES:
        session["lang"] = lang
        session.permanent = True
    target = request.form.get("next", "")
    # Only allow redirects back into this site.
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        target = url_for("dashboard")
    return redirect(target)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("not_found.html"), 404


# ------------------------------------------------------------ Filter helpers
RECENCY = [("day", "Last 24 hours", 1), ("week", "Last week", 7), ("month", "Last month", 30)]
RECENCY_OPTIONS = [(value, label) for value, label, _ in RECENCY]
RECENCY_DAYS = {value: days for value, _, days in RECENCY}
SALARY_OPTIONS = [(n, f"${n:,}+") for n in (40000, 60000, 80000, 100000, 120000)]


def arg(name):
    """A query-string value (?name=...), trimmed; '' when missing."""
    return request.args.get(name, "").strip()


def like(term):
    """Wrap a search term for LIKE, escaping % and _ so they match literally."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def since(recency):
    """'day' / 'week' / 'month' -> the earliest date to include (None if no filter)."""
    days = RECENCY_DAYS.get(recency)
    return date.today() - timedelta(days=days) if days else None


def where_sql(conditions):
    return ("WHERE " + " AND ".join(conditions)) if conditions else ""


# ---------------------------------------------------------------- Dashboard
@app.route("/")
def dashboard():
    counts = query(
        """
        SELECT
            (SELECT COUNT(*) FROM companies)    AS companies,
            (SELECT COUNT(*) FROM jobs)         AS jobs,
            (SELECT COUNT(*) FROM applications) AS applications,
            (SELECT COUNT(*) FROM contacts)     AS contacts
        """,
        one=True,
    )
    by_status = query(
        "SELECT status, COUNT(*) AS count FROM applications "
        "GROUP BY status ORDER BY count DESC"
    )
    recent = query(
        """
        SELECT a.application_id, a.application_date, a.status,
               j.job_title, c.company_name
        FROM applications a
        JOIN jobs j      ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        ORDER BY a.application_date DESC
        LIMIT 5
        """
    )
    return render_template(
        "dashboard.html", counts=counts, by_status=by_status, recent=recent
    )


# ---------------------------------------------------------------- Companies
COMPANY_LIMITS = {"company_name": 100, "industry": 50, "website": 200,
                  "city": 50, "state": 50}
COMPANY_LABELS = {"company_name": "Company name", "industry": "Industry",
                  "website": "Website", "city": "City", "state": "State"}


def validate_company(form):
    """Return a list of error messages (empty list means the form is valid)."""
    errors = []
    if not form.get("company_name", "").strip():
        errors.append(tr("Company name is required."))
    for field, limit in COMPANY_LIMITS.items():
        if len(form.get(field, "").strip()) > limit:
            errors.append(tr("{label} must be {limit} characters or fewer.",
                             label=tr(COMPANY_LABELS[field]), limit=limit))
    website = form.get("website", "").strip()
    if website and not website.lower().startswith(("http://", "https://")):
        errors.append(tr("Website must start with http:// or https://."))
    return errors


def company_values(form):
    """Pull the company fields out of a form; empty strings become NULL."""
    get = lambda name: form.get(name, "").strip() or None
    return (get("company_name"), get("industry"), get("website"),
            get("city"), get("state"), get("notes"))


def get_company_or_404(company_id):
    company = query("SELECT * FROM companies WHERE company_id = %s",
                    (company_id,), one=True)
    if company is None:
        abort(404)
    return company


@app.route("/companies")
def companies():
    q, location, industry = arg("q"), arg("location"), arg("industry")
    where, params = [], []
    if q:
        where.append("(c.company_name LIKE %s OR c.industry LIKE %s "
                     "OR c.city LIKE %s OR c.state LIKE %s)")
        params += [like(q)] * 4
    if location:
        where.append("CONCAT_WS(', ', c.city, c.state) = %s")
        params.append(location)
    if industry:
        where.append("c.industry = %s")
        params.append(industry)

    rows = query(
        f"""
        SELECT c.*,
               GROUP_CONCAT(DISTINCT CONCAT(j.job_title, CHAR(9), a.status)
                            ORDER BY j.job_title SEPARATOR '\n') AS roles_applied,
               (SELECT COUNT(*) FROM jobs j2     WHERE j2.company_id = c.company_id) AS job_count,
               (SELECT COUNT(*) FROM contacts k WHERE k.company_id = c.company_id) AS contact_count
        FROM companies c
        LEFT JOIN jobs j         ON j.company_id = c.company_id
        LEFT JOIN applications a ON a.job_id = j.job_id
        {where_sql(where)}
        GROUP BY c.company_id
        ORDER BY c.company_name
        """,
        tuple(params),
    )
    for row in rows:
        row["roles"] = [dict(zip(("title", "status"), line.split("\t", 1)))
                        for line in (row["roles_applied"] or "").split("\n") if line]
    locations = [(r["location"], r["location"]) for r in query(
        "SELECT DISTINCT CONCAT_WS(', ', city, state) AS location FROM companies "
        "WHERE city IS NOT NULL OR state IS NOT NULL ORDER BY location")]
    industries = [(r["industry"], r["industry"]) for r in query(
        "SELECT DISTINCT industry FROM companies "
        "WHERE industry IS NOT NULL AND industry <> '' ORDER BY industry")]
    filters = {"q": q, "location": location, "industry": industry,
               "active": bool(q or location or industry)}
    return render_template("companies.html", companies=rows, filters=filters,
                           location_opts=locations, industry_opts=industries)


@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    company = get_company_or_404(company_id)
    jobs = query("SELECT * FROM jobs WHERE company_id = %s ORDER BY date_posted DESC",
                 (company_id,))
    contacts = query("SELECT * FROM contacts WHERE company_id = %s ORDER BY contact_name",
                     (company_id,))
    return render_template("company_detail.html", company=company,
                           jobs=jobs, contacts=contacts)


@app.route("/companies/add", methods=["GET", "POST"])
def company_add():
    if request.method == "POST":
        errors = validate_company(request.form)
        if errors:
            return render_template("company_form.html", company=request.form,
                                   errors=errors, mode="Add")
        execute(
            "INSERT INTO companies (company_name, industry, website, city, state, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            company_values(request.form),
        )
        flash(tr("Company added."), "success")
        return redirect(url_for("companies"))
    return render_template("company_form.html", company={}, errors=[], mode="Add")


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def company_edit(company_id):
    company = get_company_or_404(company_id)
    if request.method == "POST":
        errors = validate_company(request.form)
        if errors:
            return render_template("company_form.html", company=request.form,
                                   errors=errors, mode="Edit",
                                   company_id=company_id)
        execute(
            "UPDATE companies SET company_name=%s, industry=%s, website=%s, "
            "city=%s, state=%s, notes=%s WHERE company_id=%s",
            company_values(request.form) + (company_id,),
        )
        flash(tr("Company updated."), "success")
        return redirect(url_for("companies"))
    return render_template("company_form.html", company=company, errors=[],
                           mode="Edit", company_id=company_id)


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def company_delete(company_id):
    get_company_or_404(company_id)
    execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
    flash(tr("Company deleted."), "success")
    return redirect(url_for("companies"))


# --------------------------------------------------------------------- Jobs
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]


def parse_skills(value):
    """Turn the JSON stored in jobs.requirements into a Python list."""
    if value is None:
        return []
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def split_skills(text):
    """'Python, SQL, python' -> ['Python', 'SQL'] (trimmed, no duplicates)."""
    seen, skills = set(), []
    for part in text.split(","):
        skill = part.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def validate_job(form):
    errors = []
    company_id = form.get("company_id", "").strip()
    if not company_id.isdigit() or not query(
            "SELECT 1 FROM companies WHERE company_id = %s", (company_id,), one=True):
        errors.append(tr("Choose a company from the list."))

    title = form.get("job_title", "").strip()
    if not title:
        errors.append(tr("Job title is required."))
    elif len(title) > 100:
        errors.append(tr("Job title must be 100 characters or fewer."))

    job_type = form.get("job_type", "").strip()
    if job_type and job_type not in JOB_TYPES:
        errors.append(tr("Job type must be one of: {types}.",
                         types=", ".join(tr(t) for t in JOB_TYPES)))

    salaries = {}
    for field, label in (("salary_min", "Minimum salary"), ("salary_max", "Maximum salary")):
        value = form.get(field, "").strip()
        if value:
            if not value.isdigit() or int(value) > 10_000_000:
                errors.append(tr("{label} must be a whole number of 0 or more.", label=tr(label)))
            else:
                salaries[field] = int(value)
    if len(salaries) == 2 and salaries["salary_min"] > salaries["salary_max"]:
        errors.append(tr("Minimum salary cannot be higher than maximum salary."))

    url = form.get("job_url", "").strip()
    if len(url) > 300:
        errors.append(tr("Job URL must be 300 characters or fewer."))
    elif url and not url.lower().startswith(("http://", "https://")):
        errors.append(tr("Job URL must start with http:// or https://."))

    posted = form.get("date_posted", "").strip()
    if posted:
        try:
            datetime.strptime(posted, "%Y-%m-%d")
        except ValueError:
            errors.append(tr("Date posted must be a valid date."))

    skills = split_skills(form.get("requirements", ""))
    if len(skills) > 30 or any(len(k) > 50 for k in skills):
        errors.append(tr("Requirements: up to 30 skills, each 50 characters or fewer."))
    return errors


def job_values(form):
    """Convert a validated form into the tuple the INSERT/UPDATE expects."""
    get = lambda name: form.get(name, "").strip() or None
    to_int = lambda name: int(form[name]) if form.get(name, "").strip() else None
    skills = split_skills(form.get("requirements", ""))
    return (int(form["company_id"]), form["job_title"].strip(), get("job_type"),
            to_int("salary_min"), to_int("salary_max"), get("job_url"),
            get("date_posted"), json.dumps(skills) if skills else None)


def company_options():
    return query("SELECT company_id, company_name FROM companies ORDER BY company_name")


def get_job_or_404(job_id):
    job = query("SELECT * FROM jobs WHERE job_id = %s", (job_id,), one=True)
    if job is None:
        abort(404)
    return job


@app.route("/jobs")
def jobs():
    q, company, job_type = arg("q"), arg("company"), arg("type")
    salary, posted = arg("salary"), arg("posted")
    where, params = [], []
    if q:
        where.append("(j.job_title LIKE %s OR c.company_name LIKE %s "
                     "OR CAST(j.requirements AS CHAR) LIKE %s)")
        params += [like(q)] * 3
    if company.isdigit():
        where.append("j.company_id = %s")
        params.append(int(company))
    if job_type in JOB_TYPES:
        where.append("j.job_type = %s")
        params.append(job_type)
    if salary.isdigit():
        where.append("COALESCE(j.salary_max, j.salary_min) >= %s")
        params.append(int(salary))
    earliest = since(posted)
    if earliest:
        where.append("j.date_posted >= %s")
        params.append(earliest)

    rows = query(
        f"""
        SELECT j.*, c.company_name,
               (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS application_count
        FROM jobs j
        JOIN companies c ON j.company_id = c.company_id
        {where_sql(where)}
        ORDER BY j.date_posted DESC, j.job_title
        """,
        tuple(params),
    )
    for row in rows:
        row["skills"] = parse_skills(row["requirements"])

    # The chart and industry list always describe all jobs, not just the filtered ones.
    by_type = query(
        "SELECT COALESCE(job_type, 'Not specified') AS type_name, COUNT(*) AS total "
        "FROM jobs GROUP BY type_name ORDER BY total DESC, type_name"
    )
    by_industry = query(
        "SELECT COALESCE(c.industry, 'Not specified') AS industry_name, COUNT(*) AS total "
        "FROM jobs j JOIN companies c ON j.company_id = c.company_id "
        "GROUP BY industry_name ORDER BY total DESC, industry_name"
    )
    for row in by_industry:
        if row["industry_name"] == "Not specified":
            row["industry_name"] = tr("Not specified")
    chart = {
        "labels": [f"{tr(r['type_name'])} ({r['total']})" for r in by_type],
        "counts": [r["total"] for r in by_type],
        "types": [r["type_name"] for r in by_type],
    }
    filters = {"q": q, "company": company, "type": job_type, "salary": salary,
               "posted": posted,
               "active": bool(q or company or job_type or salary or posted)}
    return render_template(
        "jobs.html", jobs=rows, chart=chart, by_type=by_type, by_industry=by_industry,
        filters=filters,
        company_opts=[(c["company_id"], c["company_name"]) for c in company_options()],
        type_opts=[(t, tr(t)) for t in JOB_TYPES],
        salary_opts=SALARY_OPTIONS,
        recency_opts=[(v, tr(label)) for v, label in RECENCY_OPTIONS])


@app.route("/jobs/add", methods=["GET", "POST"])
def job_add():
    options = company_options()
    if request.method == "POST":
        errors = validate_job(request.form)
        if errors:
            return render_template("job_form.html", job=request.form, errors=errors,
                                   mode="Add", companies=options, job_types=JOB_TYPES)
        execute(
            "INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, "
            "job_url, date_posted, requirements) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            job_values(request.form),
        )
        flash(tr("Job added."), "success")
        return redirect(url_for("jobs"))
    return render_template("job_form.html", job={}, errors=[], mode="Add",
                           companies=options, job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def job_edit(job_id):
    job = get_job_or_404(job_id)
    options = company_options()
    if request.method == "POST":
        errors = validate_job(request.form)
        if errors:
            return render_template("job_form.html", job=request.form, errors=errors,
                                   mode="Edit", companies=options, job_types=JOB_TYPES)
        execute(
            "UPDATE jobs SET company_id=%s, job_title=%s, job_type=%s, salary_min=%s, "
            "salary_max=%s, job_url=%s, date_posted=%s, requirements=%s WHERE job_id=%s",
            job_values(request.form) + (job_id,),
        )
        flash(tr("Job updated."), "success")
        return redirect(url_for("jobs"))
    values = dict(job)
    values["requirements"] = ", ".join(parse_skills(job["requirements"]))
    return render_template("job_form.html", job=values, errors=[], mode="Edit",
                           companies=options, job_types=JOB_TYPES)


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def job_delete(job_id):
    get_job_or_404(job_id)
    execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    flash(tr("Job deleted."), "success")
    return redirect(url_for("jobs"))


# ------------------------------------------------------------- Applications
APPLICATION_STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
# form field name -> key inside applications.interview_data (JSON)
INTERVIEW_FIELDS = {"round": "interview_round", "type": "interview_type",
                    "interviewer": "interviewer", "date": "interview_date",
                    "notes": "interview_notes"}


def parse_json_object(value):
    """Turn the JSON stored in applications.interview_data into a dict."""
    if value is None:
        return {}
    if isinstance(value, (bytes, bytearray)):
        value = value.decode()
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def valid_date(text):
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_application(form):
    errors = []
    job_id = form.get("job_id", "").strip()
    if not job_id.isdigit() or not query(
            "SELECT 1 FROM jobs WHERE job_id = %s", (job_id,), one=True):
        errors.append(tr("Choose a job from the list."))

    applied = form.get("application_date", "").strip()
    if not applied:
        errors.append(tr("Date applied is required."))
    elif not valid_date(applied):
        errors.append(tr("Date applied must be a valid date."))

    if form.get("status", "").strip() not in APPLICATION_STATUSES:
        errors.append(tr("Status must be one of: {statuses}.",
                         statuses=", ".join(tr(x) for x in APPLICATION_STATUSES)))

    if len(form.get("resume_version", "").strip()) > 50:
        errors.append(tr("Resume version must be 50 characters or fewer."))

    rnd = form.get("interview_round", "").strip()
    if rnd and (not rnd.isdigit() or not 1 <= int(rnd) <= 20):
        errors.append(tr("Interview round must be a number from 1 to 20."))
    if len(form.get("interview_type", "").strip()) > 50:
        errors.append(tr("Interview type must be 50 characters or fewer."))
    if len(form.get("interviewer", "").strip()) > 100:
        errors.append(tr("Interviewer must be 100 characters or fewer."))
    when = form.get("interview_date", "").strip()
    if when and not valid_date(when):
        errors.append(tr("Interview date must be a valid date."))
    if len(form.get("interview_notes", "").strip()) > 500:
        errors.append(tr("Interview notes must be 500 characters or fewer."))
    return errors


def build_interview(form, existing=None):
    """Form fields -> JSON text for interview_data (None when everything is blank).

    Keys the form doesn't know about are kept, so editing never loses data."""
    data = dict(existing or {})
    for key, field in INTERVIEW_FIELDS.items():
        value = form.get(field, "").strip()
        if value:
            data[key] = int(value) if key == "round" else value
        else:
            data.pop(key, None)
    return json.dumps(data) if data else None


def application_values(form, existing=None):
    return (int(form["job_id"]), form["application_date"].strip(), form["status"].strip(),
            form.get("resume_version", "").strip() or None,
            1 if form.get("cover_letter_sent") else 0,
            build_interview(form, existing))


def job_options():
    return query(
        "SELECT j.job_id, j.job_title, c.company_name FROM jobs j "
        "JOIN companies c ON j.company_id = c.company_id "
        "ORDER BY c.company_name, j.job_title"
    )


def get_application_or_404(application_id):
    row = query("SELECT * FROM applications WHERE application_id = %s",
                (application_id,), one=True)
    if row is None:
        abort(404)
    return row


@app.route("/applications")
def applications():
    q, company, applied, status = arg("q"), arg("company"), arg("applied"), arg("status")
    where, params = [], []
    if q:
        where.append("(j.job_title LIKE %s OR c.company_name LIKE %s)")
        params += [like(q)] * 2
    if company.isdigit():
        where.append("c.company_id = %s")
        params.append(int(company))
    earliest = since(applied)
    if earliest:
        where.append("a.application_date >= %s")
        params.append(earliest)
    if status in APPLICATION_STATUSES:
        where.append("a.status = %s")
        params.append(status)

    rows = query(
        f"""
        SELECT a.application_id, a.application_date, a.status,
               j.job_title, c.company_name
        FROM applications a
        JOIN jobs j      ON a.job_id = j.job_id
        JOIN companies c ON j.company_id = c.company_id
        {where_sql(where)}
        ORDER BY a.application_date DESC, a.application_id DESC
        """,
        tuple(params),
    )
    # The status bars always describe all applications, not just the filtered ones.
    counts = {r["status"]: r["total"] for r in query(
        "SELECT status, COUNT(*) AS total FROM applications GROUP BY status")}
    biggest = max(counts.values(), default=0) or 1
    summary = [{"status": s, "total": counts.get(s, 0),
                "pct": round(counts.get(s, 0) / biggest * 100)}
               for s in APPLICATION_STATUSES]
    filters = {"q": q, "company": company, "applied": applied, "status": status,
               "active": bool(q or company or applied or status)}
    return render_template(
        "applications.html", applications=rows, summary=summary, filters=filters,
        company_opts=[(c["company_id"], c["company_name"]) for c in company_options()],
        recency_opts=[(v, tr(label)) for v, label in RECENCY_OPTIONS],
        status_opts=[(x, tr(x)) for x in APPLICATION_STATUSES])


@app.route("/applications/add", methods=["GET", "POST"])
def application_add():
    options = job_options()
    if request.method == "POST":
        errors = validate_application(request.form)
        if errors:
            return render_template("application_form.html", application=request.form,
                                   errors=errors, mode="Add", jobs=options,
                                   statuses=APPLICATION_STATUSES)
        execute(
            "INSERT INTO applications (job_id, application_date, status, resume_version, "
            "cover_letter_sent, interview_data) VALUES (%s, %s, %s, %s, %s, %s)",
            application_values(request.form),
        )
        flash(tr("Application added."), "success")
        return redirect(url_for("applications"))
    defaults = {"application_date": date.today().isoformat(), "status": "Applied"}
    return render_template("application_form.html", application=defaults, errors=[],
                           mode="Add", jobs=options, statuses=APPLICATION_STATUSES)


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def application_edit(application_id):
    row = get_application_or_404(application_id)
    options = job_options()
    existing = parse_json_object(row["interview_data"])
    if request.method == "POST":
        errors = validate_application(request.form)
        if errors:
            return render_template("application_form.html", application=request.form,
                                   errors=errors, mode="Edit", jobs=options,
                                   statuses=APPLICATION_STATUSES)
        execute(
            "UPDATE applications SET job_id=%s, application_date=%s, status=%s, "
            "resume_version=%s, cover_letter_sent=%s, interview_data=%s "
            "WHERE application_id=%s",
            application_values(request.form, existing) + (application_id,),
        )
        flash(tr("Application updated."), "success")
        return redirect(url_for("applications"))
    values = dict(row)
    for key, field in INTERVIEW_FIELDS.items():
        values[field] = existing.get(key, "")
    return render_template("application_form.html", application=values, errors=[],
                           mode="Edit", jobs=options, statuses=APPLICATION_STATUSES)


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def application_delete(application_id):
    get_application_or_404(application_id)
    execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
    flash(tr("Application deleted."), "success")
    return redirect(url_for("applications"))


# ------------------------------------------------------------------ Contacts
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def validate_contact(form):
    errors = []
    company_id = form.get("company_id", "").strip()
    if not company_id.isdigit() or not query(
            "SELECT 1 FROM companies WHERE company_id = %s", (company_id,), one=True):
        errors.append(tr("Choose a company from the list."))

    name = form.get("contact_name", "").strip()
    if not name:
        errors.append(tr("Name is required."))
    elif len(name) > 100:
        errors.append(tr("Name must be 100 characters or fewer."))

    if len(form.get("title", "").strip()) > 100:
        errors.append(tr("Job title must be 100 characters or fewer."))
    email = form.get("email", "").strip()
    if len(email) > 100:
        errors.append(tr("Email must be 100 characters or fewer."))
    elif email and not EMAIL_PATTERN.fullmatch(email):
        errors.append(tr("Email doesn't look right (example: name@company.com)."))
    if len(form.get("phone", "").strip()) > 20:
        errors.append(tr("Phone must be 20 characters or fewer."))
    linkedin = form.get("linkedin_url", "").strip()
    if len(linkedin) > 200:
        errors.append(tr("LinkedIn URL must be 200 characters or fewer."))
    elif linkedin and not linkedin.lower().startswith(("http://", "https://")):
        errors.append(tr("LinkedIn URL must start with http:// or https://."))
    return errors


def contact_values(form):
    get = lambda name: form.get(name, "").strip() or None
    return (int(form["company_id"]), form["contact_name"].strip(), get("title"),
            get("email"), get("phone"), get("linkedin_url"), get("notes"))


def get_contact_or_404(contact_id):
    row = query("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,), one=True)
    if row is None:
        abort(404)
    return row


@app.route("/contacts")
def contacts():
    q = arg("q")
    where, params = [], []
    if q:
        where.append("(k.contact_name LIKE %s OR k.title LIKE %s "
                     "OR c.company_name LIKE %s OR k.email LIKE %s)")
        params += [like(q)] * 4
    rows = query(
        f"""
        SELECT k.contact_id, k.contact_name, k.title, k.email, c.company_name
        FROM contacts k
        JOIN companies c ON k.company_id = c.company_id
        {where_sql(where)}
        ORDER BY k.contact_name
        """,
        tuple(params),
    )
    return render_template("contacts.html", contacts=rows,
                           filters={"q": q, "active": bool(q)})


@app.route("/contacts/add", methods=["GET", "POST"])
def contact_add():
    options = company_options()
    if request.method == "POST":
        errors = validate_contact(request.form)
        if errors:
            return render_template("contact_form.html", contact=request.form,
                                   errors=errors, mode="Add", companies=options)
        execute(
            "INSERT INTO contacts (company_id, contact_name, title, email, phone, "
            "linkedin_url, notes) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            contact_values(request.form),
        )
        flash(tr("Contact added."), "success")
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact={}, errors=[], mode="Add",
                           companies=options)


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def contact_edit(contact_id):
    row = get_contact_or_404(contact_id)
    options = company_options()
    if request.method == "POST":
        errors = validate_contact(request.form)
        if errors:
            return render_template("contact_form.html", contact=request.form,
                                   errors=errors, mode="Edit", companies=options)
        execute(
            "UPDATE contacts SET company_id=%s, contact_name=%s, title=%s, email=%s, "
            "phone=%s, linkedin_url=%s, notes=%s WHERE contact_id=%s",
            contact_values(request.form) + (contact_id,),
        )
        flash(tr("Contact updated."), "success")
        return redirect(url_for("contacts"))
    return render_template("contact_form.html", contact=row, errors=[], mode="Edit",
                           companies=options)


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def contact_delete(contact_id):
    get_contact_or_404(contact_id)
    execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
    flash(tr("Contact deleted."), "success")
    return redirect(url_for("contacts"))


# ----------------------------------------------------------------- Job Match
@app.route("/job-match")
def job_match():
    user_skills = split_skills(arg("skills"))
    have = {skill.lower() for skill in user_skills}

    rows = query(
        "SELECT j.job_id, j.job_title, j.job_url, j.requirements, c.company_name "
        "FROM jobs j JOIN companies c ON j.company_id = c.company_id"
    )
    known_skills = {}          # every skill mentioned by any job (for the hint under the box)
    results, without_requirements = [], 0
    for row in rows:
        required = [str(skill) for skill in parse_skills(row["requirements"])]
        for skill in required:
            known_skills.setdefault(skill.lower(), skill)
        if not required:
            without_requirements += 1
            continue
        matched = [s for s in required if s.lower() in have]
        missing = [s for s in required if s.lower() not in have]
        results.append({
            "job_title": row["job_title"], "company_name": row["company_name"],
            "job_url": row["job_url"], "matched": matched, "missing": missing,
            "total": len(required), "pct": round(len(matched) / len(required) * 100),
        })
    # Best match first; on a tie, the job where you match more skills; then by title.
    results.sort(key=lambda r: (-r["pct"], -len(r["matched"]), r["job_title"].lower()))

    return render_template(
        "job_match.html", skills_text=arg("skills"), searched=bool(user_skills),
        user_skills=user_skills, results=results,
        without_requirements=without_requirements,
        known_skills=sorted(known_skills.values(), key=str.lower))


if __name__ == "__main__":
    app.run(debug=True)
