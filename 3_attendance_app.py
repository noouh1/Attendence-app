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


def get_conn():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS people (
        unique_id TEXT PRIMARY KEY, name TEXT, email TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance (
        unique_id TEXT PRIMARY KEY, attended INTEGER DEFAULT 0, attend_time TEXT)""")

    count = c.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    if count == 0:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, dtype={"unique_id": str})
            imported = 0
            for _, row in df.iterrows():
                uid   = str(row.get("unique_id", "")).strip()
                name  = str(row.get(NAME_COLUMN, ""))
                email = str(row.get("email", ""))
                if uid:
                    c.execute("INSERT OR IGNORE INTO people VALUES (?,?,?)", (uid, name, email))
                    c.execute("INSERT OR IGNORE INTO attendance VALUES (?,0,NULL)", (uid,))
                    imported += 1
            conn.commit()
            print(f"✅ Imported {imported} people from Excel.")
        else:
            print(f"⚠️  WARNING: {EXCEL_FILE} not found. Database is empty.")
    else:
        print(f"✅ Database ready — {count} people loaded.")
    conn.close()


def get_stats():
    conn = get_conn()
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
    try:
        data = request.get_json(force=True)
        uid  = str(data.get("uid", "")).strip()

        if not uid:
            return jsonify({"success": False, "message": "❌ QR فارغ", "stats": get_stats()})

        conn = get_conn()
        person = conn.execute(
            "SELECT p.unique_id, p.name, a.attended, a.attend_time FROM people p "
            "LEFT JOIN attendance a ON p.unique_id = a.unique_id WHERE p.unique_id = ?", (uid,)
        ).fetchone()
        conn.close()

        if not person:
            return jsonify({"success": False, "message": f"❌ ID غير موجود: {uid}", "stats": get_stats()})

        p_uid, name, attended, attend_time = person

        if attended:
            return jsonify({"success": True, "already": True, "name": name, "uid": p_uid,
                            "message": f"⚠️ تم تسجيل {name} مسبقاً",
                            "time": attend_time or "", "stats": get_stats()})

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_conn()
        conn.execute("UPDATE attendance SET attended=1, attend_time=? WHERE unique_id=?", (now, p_uid))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "already": False, "name": name, "uid": p_uid,
                        "message": f"✅ تم تسجيل حضور {name}",
                        "time": now, "stats": get_stats()})
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ خطأ: {str(e)}", "stats": get_stats()}), 500


@app.route("/stats")
def stats():
    return jsonify(get_stats())


@app.route("/debug")
def debug():
    """Check database status — visit /debug to diagnose."""
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM people").fetchone()[0]
    attended = conn.execute("SELECT COUNT(*) FROM attendance WHERE attended=1").fetchone()[0]
    sample = conn.execute("SELECT unique_id, name FROM people LIMIT 5").fetchall()
    conn.close()
    excel_exists = os.path.exists(EXCEL_FILE)
    return jsonify({
        "excel_file_found": excel_exists,
        "total_people": total,
        "attended": attended,
        "sample_ids": [{"uid": r[0], "name": r[1]} for r in sample]
    })


@app.route("/export")
def export():
    try:
        conn = get_conn()
        df = pd.read_sql_query("""
            SELECT p.unique_id, p.name, p.email,
                   CASE WHEN a.attended=1 THEN 'Yes' ELSE 'No' END AS attended,
                   COALESCE(a.attend_time, '') as attend_time
            FROM people p
            LEFT JOIN attendance a ON p.unique_id = a.unique_id
        """, conn)
        conn.close()

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Attendance")
        output.seek(0)
        filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        return send_file(output, as_attachment=True, download_name=filename,
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return f"Export error: {str(e)}", 500


if __name__ == "__main__":
    print("🚀 Initializing...")
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Running on port {port}")
    app.run(debug=False, host="0.0.0.0", port=port)
