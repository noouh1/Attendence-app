"""
3_attendance_app.py — Production Version (Railway)
====================================================
- Uses SQLite database for persistent attendance (survives restarts)
- Reads people list from people_with_ids.xlsx
- Exports attendance as Excel
"""

from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import sqlite3
import os
import io
from datetime import datetime

app = Flask(__name__)

EXCEL_FILE  = "people_with_ids.xlsx"
DB_FILE     = "attendance.db"
NAME_COLUMN = "name"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS people (
        unique_id TEXT PRIMARY KEY, name TEXT, email TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        unique_id TEXT PRIMARY KEY, attended INTEGER DEFAULT 0,
        attend_time TEXT, FOREIGN KEY (unique_id) REFERENCES people(unique_id))""")

    count = c.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    if count == 0 and os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE, dtype={"unique_id": str})
        for _, row in df.iterrows():
            uid   = str(row.get("unique_id", "")).strip()
            name  = str(row.get(NAME_COLUMN, ""))
            email = str(row.get("email", ""))
            if uid:
                c.execute("INSERT OR IGNORE INTO people VALUES (?,?,?)", (uid, name, email))
                c.execute("INSERT OR IGNORE INTO attendance VALUES (?,0,NULL)", (uid,))
        print(f"   Imported {len(df)} people into database.")
    conn.commit()
    conn.close()


def get_person(uid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    row = c.execute("""
        SELECT p.unique_id, p.name, a.attended, a.attend_time
        FROM people p LEFT JOIN attendance a ON p.unique_id = a.unique_id
        WHERE p.unique_id = ?""", (uid,)).fetchone()
    conn.close()
    return row


def mark_attended(uid):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_FILE)
    conn.execute("UPDATE attendance SET attended=1, attend_time=? WHERE unique_id=?", (now, uid))
    conn.commit()
    conn.close()
    return now


def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    total    = c.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    attended = c.execute("SELECT COUNT(*) FROM attendance WHERE attended=1").fetchone()[0]
    conn.close()
    return {"total": total, "attended": attended, "remaining": total - attended}


@app.route("/")
def index():
    return render_template("scanner.html")


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    uid  = str(data.get("uid", "")).strip()
    if not uid:
        return jsonify({"success": False, "message": "❌ QR فارغ"})
    person = get_person(uid)
    if not person:
        return jsonify({"success": False, "message": f"❌ ID غير موجود: {uid}", "stats": get_stats()})
    uid, name, attended, attend_time = person
    if attended:
        return jsonify({"success": True, "already": True, "name": name, "uid": uid,
                        "message": f"⚠️ تم تسجيل {name} مسبقاً", "time": attend_time, "stats": get_stats()})
    now = mark_attended(uid)
    return jsonify({"success": True, "already": False, "name": name, "uid": uid,
                    "message": f"✅ تم تسجيل حضور {name}", "time": now, "stats": get_stats()})


@app.route("/stats")
def stats():
    return jsonify(get_stats())


@app.route("/export")
def export():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT p.unique_id, p.name, p.email,
               CASE WHEN a.attended=1 THEN 'Yes' ELSE '' END AS attended,
               a.attend_time
        FROM people p LEFT JOIN attendance a ON p.unique_id = a.unique_id
        ORDER BY a.attend_time DESC""", conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)
    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/list")
def list_attended():
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("""SELECT p.name, p.unique_id, a.attend_time
        FROM people p JOIN attendance a ON p.unique_id = a.unique_id
        WHERE a.attended=1 ORDER BY a.attend_time DESC""").fetchall()
    conn.close()
    return jsonify([{"name": r[0], "uid": r[1], "time": r[2]} for r in rows])


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Starting → http://localhost:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
