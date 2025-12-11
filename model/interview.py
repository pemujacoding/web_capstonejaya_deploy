from .connect import cursor, db
import json

def insert_new_interview_session(user_id,candidate_id):
    sql = "INSERT INTO interview (user_id, candidate_id, status) VALUES (%s,%s,'Pending')"
    cursor.execute(sql, (user_id,candidate_id))
    new_session_id = cursor.lastrowid
    db.commit() 
    return new_session_id

def update_interview(result,id) :
    sql = "UPDATE interview SET status='Succeed',result=%s WHERE id = %s"
    cursor.execute(sql, (result,id))
    db.commit()

def get_by_id(interview_id) :
    sql = "SELECT * FROM interview WHERE id = %s"
    cursor.execute(sql, (interview_id,))
    result = cursor.fetchone()
    return result

def delete_interview(interview_id) :
    sql = "DELETE FROM interview WHERE id = %s"
    cursor.execute(sql, (interview_id,))
    db.commit()

def get_for_final(user_id,interview_id) :
    sql = '''
    SELECT 
    i.id AS interview_id,
    i.user_id,
    i.candidate_id,
    i.result,
    u.full_name,
    u.email AS user_email,
    c.name,
    c.email AS candidate_email,
    c.photoUrl
    FROM interview i
    INNER JOIN users u ON i.user_id = u.id
    INNER JOIN candidates c ON i.candidate_id = c.id
    WHERE i.user_id = %s AND i.id = %s 
    '''
    cursor.execute(sql, (user_id,interview_id))
    result = cursor.fetchone()
    return result

def get_history(user_id):
    sql = '''
    SELECT 
        i.id AS interview_id,
        i.user_id,
        i.candidate_id,
        i.result,
        i.status,
        i.created_at,
        v.id AS video_id,
        v.file_name,
        v.result_cd,
        v.result_stt
    FROM interview i
    LEFT JOIN input v ON v.interview_id = i.id
    WHERE i.user_id = %s
    ORDER BY i.created_at DESC, v.id ASC;
    '''
    cursor.execute(sql, (user_id,))
    rows = cursor.fetchall()

    interviews = {}

    for r in rows:
        iid = r[0]

        # hanya buat interview sekali saja
        if iid not in interviews:
            interviews[iid] = {
                "interview_id": r[0],
                "user_id": r[1],
                "candidate_id":r[2],
                "result_interview":r[3],
                "status": r[4],
                "created_at": r[5],
                "videos": []
            }

        # tambahkan video jika ada
        if r[4] is not None:  # video_id
            interviews[iid]["videos"].append({
                "video_id": r[6],
                "file_name": r[7],
                "result_cd": r[8],
                "result_stt": r[9]
            })

    return list(interviews.values())
