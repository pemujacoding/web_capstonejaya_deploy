import mysql.connector

db = mysql.connector.connect(
    host="sql100.infinityfree.com",        # atau IP server MySQL
    user="if0_40658101",
    password="capjaya2025",
    database="if0_40658101_interview"
)

cursor = db.cursor()
print("Connected!")