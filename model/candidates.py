from .connect import cursor, db

def insert(name,email,photo) :
    sql = "INSERT INTO candidates (name,email,photoUrl) VALUES (%s,%s,%s)"
    cursor.execute(sql,(name,email,photo))
    db.commit()

def get_candidates() :
    cursor.execute("SELECT * FROM candidates")
    result = cursor.fetchall()
    return result

def get_by_id(id)  :
    sql = "SELECT * FROM candidates WHERE id=%s"
    cursor.execute(sql,(id,))
    return cursor.fetchone()

def update(candidate_id, name, email, photoUrl):
        sql = "UPDATE candidates SET name=%s, email=%s, photoUrl=%s WHERE id=%s"
        cursor.execute(sql, (name, email, photoUrl, candidate_id))
        db.commit()

def delete(candidate_id):
    sql = "DELETE FROM candidates WHERE id=%s"
    cursor.execute(sql, (candidate_id,))
    db.commit()