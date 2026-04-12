"""
Creates a sample people.xlsx for testing (10 people)
Run: python create_sample.py
"""
import pandas as pd

data = {
    "name":  ["noouh ", "nnouh ", " dima", "فاطمة خالد",
              "عمر يوسف", "نور إبراهيم", "كريم عبدالله", "هناء سعيد",
              "طارق رضا", "ليلى منصور"],
    "email": ["noouhfff@gmail.com", "noouhehab1@gmail.com", "dima.ahmed4444@example.com",
              "fatma@example.com", "omar@example.com", "nour@example.com",
              "karim@example.com", "hanaa@example.com", "tarek@example.com",
              "laila@example.com"],
    "phone": ["01001111111", "01002222222", "01003333333", "01004444444",
              "01005555555", "01006666666", "01007777777", "01008888888",
              "01009999999", "01000000000"],
}

df = pd.DataFrame(data)
df.to_excel("people.xlsx", index=False)
print("✅ people.xlsx created with", len(df), "sample entries.")
print("   Now run: python 1_generate_qr.py")
