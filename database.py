"""BACKEND: all database logic (SQLite). No screen code here."""
import sqlite3
from datetime import datetime

DB_FILE = "attendance.db"
THRESHOLD = 75  # students below this % are flagged


def run(sql, args=()):
    conn = sqlite3.connect(DB_FILE)
    try:
        rows = conn.execute(sql, args).fetchall()
        conn.commit()
        return rows
    finally:
        conn.close()


def init_db():
    run("CREATE TABLE IF NOT EXISTS students (student_id TEXT PRIMARY KEY, name TEXT NOT NULL)")
    run("""CREATE TABLE IF NOT EXISTS attendance (
               student_id TEXT, date TEXT, status TEXT,
               PRIMARY KEY (student_id, date))""")


def add_student(student_id, name):
    student_id, name = student_id.strip(), name.strip()
    if not student_id or not name:
        return False, "ID and name are required"
    if run("SELECT 1 FROM students WHERE student_id = ?", (student_id,)):
        return False, "Student ID already exists"
    run("INSERT INTO students VALUES (?, ?)", (student_id, name))
    return True, f"Added {name} ({student_id})"


def get_students():
    return run("SELECT student_id, name FROM students ORDER BY student_id")


def mark_attendance(student_id, date_text, status):
    if not run("SELECT 1 FROM students WHERE student_id = ?", (student_id,)):
        return False, "Student not found"
    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        return False, "Date must look like 2026-10-17"
    # INSERT OR REPLACE = marking the same day again just updates it
    run("INSERT OR REPLACE INTO attendance VALUES (?, ?, ?)", (student_id, date_text, status))
    return True, f"Marked {student_id} {status} on {date_text}"


def all_records():
    return run("""SELECT a.date, a.student_id, s.name, a.status
                  FROM attendance a JOIN students s ON s.student_id = a.student_id
                  ORDER BY a.date DESC, a.student_id""")


def student_summary(student_id):
    student = run("SELECT student_id, name FROM students WHERE student_id = ?", (student_id,))
    if not student:
        return None
    records = run("SELECT date, status FROM attendance WHERE student_id = ? ORDER BY date DESC",
                  (student_id,))
    total = len(records)
    present = sum(1 for _, status in records if status == "Present")
    pct = round(present / total * 100, 1) if total else 0.0
    return {"student_id": student[0][0], "name": student[0][1], "total": total,
            "present": present, "percentage": pct,
            "at_risk": total > 0 and pct < THRESHOLD, "records": records}


def insights():
    """Every student with their % and whether they are below the threshold."""
    result = []
    for student_id, name in get_students():
        s = student_summary(student_id)
        result.append((student_id, name, s["present"], s["total"], s["percentage"], s["at_risk"]))
    return result