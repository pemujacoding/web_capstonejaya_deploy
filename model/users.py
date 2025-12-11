import bcrypt
from .connect import cursor, db

def check_user(username, password):
    sql = "SELECT id, password FROM users WHERE username=%s"
    cursor.execute(sql, (username,))
    result = cursor.fetchone()

    if result:
        user_id, hashed = result
        if bcrypt.checkpw(password.encode(), hashed.encode()):
            return user_id
    return None

def create_user(username, password, fullname, email):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    sql = "INSERT INTO users (username, password, full_name, email) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (username, hashed, fullname, email))
    db.commit()

def get_by_id(user_id) :
    sql = "SELECT * FROM users WHERE id = %s"
    result = cursor.execute(sql, (user_id,))
    return result