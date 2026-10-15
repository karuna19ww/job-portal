from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("jobs.db")

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                job_type TEXT NOT NULL,
                salary TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                applicant_name TEXT NOT NULL,
                email TEXT NOT NULL,
                resume_link TEXT DEFAULT '',
                cover_letter TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            )
        """)
        count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        if count == 0:
            sample_jobs = [
                ("Python Developer Intern", "BrightByte Labs", "Bengaluru, India", "Internship", "₹10,000–₹18,000/month", "Help build Python APIs, write tests, and work with a small product team."),
                ("Frontend Developer", "PixelCraft", "Remote", "Full-time", "₹4–7 LPA", "Build accessible, responsive interfaces using HTML, CSS, JavaScript, and modern frontend practices."),
                ("Data Analyst Intern", "InsightWorks", "Hyderabad, India", "Internship", "₹12,000–₹20,000/month", "Clean datasets, prepare dashboards, and communicate useful insights to business teams."),
                ("Junior Java Developer", "Northstar Systems", "Chennai, India", "Full-time", "₹3.5–5.5 LPA", "Develop and maintain Java applications while learning testing, databases, and APIs."),
                ("UI/UX Design Intern", "Form & Function", "Remote", "Internship", "₹8,000–₹15,000/month", "Support user research, wireframes, prototypes, and design-system documentation."),
                ("Machine Learning Trainee", "Nova Analytics", "Pune, India", "Contract", "₹20,000–₹30,000/month", "Assist with data preparation, model evaluation, and reproducible ML experiments.")
            ]
            conn.executemany("""
                INSERT INTO jobs (title, company, location, job_type, salary, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, sample_jobs)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    search = request.args.get("search", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("type", "").strip()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if search:
        query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    if location:
        query += " AND location LIKE ?"
        params.append(f"%{location}%")
    if job_type and job_type != "All types":
        query += " AND job_type = ?"
        params.append(job_type)
    query += " ORDER BY created_at DESC, id DESC"
    with connect_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return jsonify([dict(row) for row in rows])

@app.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True) or {}
    required = ["title", "company", "location", "job_type", "salary", "description"]
    if any(not str(data.get(field, "")).strip() for field in required):
        return jsonify({"error": "Please fill in every job field."}), 400
    with connect_db() as conn:
        cur = conn.execute("""
            INSERT INTO jobs (title, company, location, job_type, salary, description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, tuple(str(data[field]).strip() for field in required))
        job_id = cur.lastrowid
        job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return jsonify(dict(job)), 201

@app.route("/api/jobs/<int:job_id>/apply", methods=["POST"])
def apply_to_job(job_id):
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    resume_link = str(data.get("resume_link", "")).strip()
    cover_letter = str(data.get("cover_letter", "")).strip()
    if not name or not email or "@" not in email:
        return jsonify({"error": "Enter your name and a valid email address."}), 400
    with connect_db() as conn:
        job = conn.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return jsonify({"error": "This job no longer exists."}), 404
        conn.execute("""
            INSERT INTO applications (job_id, applicant_name, email, resume_link, cover_letter)
            VALUES (?, ?, ?, ?, ?)
        """, (job_id, name, email, resume_link, cover_letter))
    return jsonify({"message": "Application submitted successfully!"}), 201

@app.route("/api/employer/applications", methods=["GET"])
def get_applications():
    # Demo endpoint: add authentication before using this with real applicant data.
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT applications.id, jobs.title, jobs.company, applications.applicant_name,
                   applications.email, applications.resume_link, applications.cover_letter,
                   applications.created_at
            FROM applications JOIN jobs ON jobs.id = applications.job_id
            ORDER BY applications.created_at DESC
        """).fetchall()
    return jsonify([dict(row) for row in rows])

init_db()

if __name__ == "__main__":
    app.run(debug=True)
