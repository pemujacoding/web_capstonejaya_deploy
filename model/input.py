from .connect import cursor, db
import json

def insert_video_bytes(file_name,result_cd,result_stt,interview_id):
    json_cd = json.dumps(result_cd)
    json_stt = json.dumps(result_stt)
    sql = "INSERT INTO input (file_name,result_cd, result_stt, interview_id) VALUES (%s,%s,%s,%s)"
    cursor.execute(sql, (file_name,json_cd,json_stt,interview_id))
    db.commit()

def get_video_by_id(input_id):
    sql= "SELECT video_file FROM input WHERE id=%s"
    cursor.execute(sql, (input_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_audio_by_id(input_id):
    sql= "SELECT audio_file FROM input WHERE id=%s"
    cursor.execute(sql, (input_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_name_by_id(input_id):
    sql= "SELECT nama_file FROM input WHERE id=%s"
    cursor.execute(sql, (input_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_videos_id(user_id):
    sql = "SELECT id, nama_file FROM input WHERE user_id = %s"
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()
    return results

