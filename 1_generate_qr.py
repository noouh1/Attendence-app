"""
STEP 1 — Generate QR Codes
===========================
- Reads your Excel file (people.xlsx)
- Adds a unique ID to each person
- Creates a QR code image for every person in /qr_codes/
- Saves updated sheet as people_with_ids.xlsx

HOW TO RUN:
    pip install -r requirements.txt
    python 1_generate_qr.py
"""

import pandas as pd
import qrcode
import os

# ─── CONFIG ──────────────────────────────────────────────
EXCEL_FILE     = "people.xlsx"       # ← your input file
OUTPUT_EXCEL   = "people_with_ids.xlsx"
QR_FOLDER      = "qr_codes"
NAME_COLUMN    = "name"              # ← column name for names
EMAIL_COLUMN   = "email"             # ← column name for emails
# ─────────────────────────────────────────────────────────

def generate_qr_codes():
    # 1. Load Excel
    print(f"📂 Loading {EXCEL_FILE}...")
    df = pd.read_excel(EXCEL_FILE)
    print(f"   Found {len(df)} people.")

    # 2. Add unique IDs (skip if already exists)
    if "unique_id" not in df.columns:
        df.insert(0, "unique_id", [f"P{i+1:04d}" for i in range(len(df))])
        print("   ✅ Unique IDs created.")

    # 3. Add attended column if missing
    if "attended" not in df.columns:
        df["attended"] = ""
    if "attend_time" not in df.columns:
        df["attend_time"] = ""

    # 4. Create QR codes folder
    os.makedirs(QR_FOLDER, exist_ok=True)

    # 5. Generate one QR per person
    print(f"\n🔄 Generating QR codes → /{QR_FOLDER}/")
    for _, row in df.iterrows():
        uid   = row["unique_id"]
        name  = row.get(NAME_COLUMN, uid)

        # QR content = just the unique ID (simple & reliable)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(uid)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"{QR_FOLDER}/{uid}.png")

    print(f"   ✅ {len(df)} QR codes saved in /{QR_FOLDER}/")

    # 6. Save updated Excel
    df.to_excel(OUTPUT_EXCEL, index=False)
    print(f"\n💾 Updated sheet saved → {OUTPUT_EXCEL}")
    print("\n✅ DONE! Now run: python 2_send_emails.py")


if __name__ == "__main__":
    generate_qr_codes()
