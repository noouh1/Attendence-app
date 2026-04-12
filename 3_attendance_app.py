"""
STEP 3 — Attendance Web App (Flask)
=====================================
- Opens a camera to scan QR codes
- Marks attendance in real-time in people_with_ids.xlsx
- Shows live stats dashboard

HOW TO RUN:
    python 3_attendance_app.py
    Then open: http://localhost:5000

DEPLOY (optional):
    Use ngrok for public access: ngrok http 5000
"""

from flask import Flask, request, jsonify, render_template, send_file
import pandas as pd
import openpyxl
from datetime import datetime
import os
import io

app = Flask(__name__)

# ─── CONFIG ──────────────────────────────────────────────
EXCEL_FILE   = "people_with_ids.xlsx"
NAME_COLUMN  = "name"
# ─────────────────────────────────────────────────────────


def load_df():
    return pd.read_excel(EXCEL_FILE, dtype={"unique_id": str})


def save_attendance(uid):
    """Mark a person as attended, return their info."""
    df = load_df()

    mask = df["unique_id"].str.strip() == uid.strip()
    matches = df[mask]

    if matches.empty:
        return {"success": False, "message": f"❌ ID غير موجود: {uid}"}

    idx = matches.index[0]
    name = str(df.at[idx, NAME_COLUMN])

    # Already attended?
    already = str(df.at[idx, "attended"]).strip().lower() in ["yes", "true", "1", "نعم"]
    if already:
        attend_time = str(df.at[idx, "attend_time"])
        return {
            "success": True,
            "already": True,
            "name": name,
            "uid": uid,
            "message": f"⚠️ تم تسجيل {name} مسبقاً",
            "time": attend_time
        }

    # Mark attendance
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.at[idx, "attended"]    = "Yes"
    df.at[idx, "attend_time"] = now
    df.to_excel(EXCEL_FILE, index=False)

    return {
        "success": True,
        "already": False,
        "name": name,
        "uid": uid,
        "message": f"✅ تم تسجيل حضور {name}",
        "time": now
    }


def get_stats():
    df = load_df()
    total    = len(df)
    attended = df["attended"].str.strip().str.lower().isin(["yes", "true", "1", "نعم"]).sum()
    return {"total": int(total), "attended": int(attended), "remaining": int(total - attended)}


# ─── ROUTES ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("scanner.html")


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    uid  = data.get("uid", "").strip()
    if not uid:
        return jsonify({"success": False, "message": "❌ QR فارغ"})
    result = save_attendance(uid)
    result["stats"] = get_stats()
    return jsonify(result)


@app.route("/stats")
def stats():
    return jsonify(get_stats())


@app.route("/export")
def export():
    """Download current attendance Excel."""
    return send_file(
        EXCEL_FILE,
        as_attachment=True,
        download_name=f"attendance_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )


@app.route("/list")
def list_attended():
    """Return list of attended people."""
    df = load_df()
    attended = df[df["attended"].str.strip().str.lower().isin(["yes", "true", "1", "نعم"])]
    people = attended[[NAME_COLUMN, "unique_id", "attend_time"]].to_dict(orient="records")
    return jsonify(people)


if __name__ == "__main__":
    if not os.path.exists(EXCEL_FILE):
        print(f"❌ ERROR: {EXCEL_FILE} not found. Run 1_generate_qr.py first.")
    else:
        print("🚀 Starting Attendance App...")
        print("   Open: http://localhost:5000")
        app.run(debug=True, host="0.0.0.0", port=5000)
