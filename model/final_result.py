from .connect import cursor, db

def get_by_id(interview_id) : 
    sql = "SELECT * FROM final_result WHERE interview_id = %s;"
    cursor.execute(sql,(interview_id,))
    result = cursor.fetchone()
    return result

