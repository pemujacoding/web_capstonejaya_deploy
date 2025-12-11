import tempfile
import os
import json
import model.input as conn_input
import subprocess
from . import yolo
from . import stt

def compress_video(input_path, output_path):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vcodec", "libx264",
        "-crf", "28", 
        "-preset", "veryfast",
        "-acodec", "aac",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print("FFmpeg error:", result.stderr.decode())
        return False

    return True

def extract_audio(video_path, audio_path):
    try:
        cmd = [
            "ffmpeg",
            "-y",                     # overwrite output
            "-i", video_path,         # input
            "-vn",                    # no video
            "-acodec", "pcm_s16le",   # WAV format
            "-ar", "16000",           # sampling rate
            "-ac", "1",               # mono
            audio_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            print("FFmpeg error:", result.stderr.decode())
            return False

        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 0

    except Exception as e:
        print("Exception:", e)
        return False

def save_video_temp(video_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_bytes)
    tmp.close()
    return tmp.name

def create_temp_path(suffix):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # penting: file descriptor ditutup biar tidak terkunci
    return path

    
def input_files(video_path,filename,ext,interview_id,question):
    if ext not in [".mp4", ".webm"]:
        print("Ext invalid")
        return None, None

    audio_path = create_temp_path(".wav")

    try:

        # extract audio
        if not extract_audio(video_path, audio_path):
            print("audio extraction failed")
            return None, None

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # run ai
        result_cd = yolo.run_detection(video_path)
        result_stt = stt.speech_to_text(audio_bytes, os.path.basename(video_path), question)

        conn_input.insert_video_bytes(
            filename,
            result_cd,
            result_stt,
            interview_id
        )

        return result_cd, result_stt

    finally:
        for p in [video_path, audio_path]:
            if os.path.exists(p):
                os.remove(p)


def final_result(output,c_id,c_name,c_email,c_photoUrl,u_id,u_name,u_email,project,cert,decision,date,status) :
    try:
        gemini_output_string = str(output)
        print("✅ Berhasil mengambil data dari variabel 'output'.")
    except NameError:
        print("❌ Error: Variabel 'output' tidak ditemukan! Harap jalankan cell Gemini API di atas dulu.")
        gemini_output_string = "{}" # Fallback kosong biar ga crash parah

    candidate_info = {
        "id": c_id,
        "name": c_name,
        "email": c_email,
        "photoUrl": c_photoUrl
    }

    cert_info = {
        "normalType": cert,
        "status": status
    }

    review_meta = {
        "assessorProfile": {"name": u_name, "id": u_id, "email": u_email},
        "decision": decision,
        "reviewedAt": date,
        "project": project,
        "overall_notes": "Kandidat memiliki pemahaman teknis yang kuat."
    }

    try:
        # A. Bersihkan Markdown ```json ... ``` dari string output
        clean_text = gemini_output_string.replace("```json", "").replace("```", "").strip()

        # B. Parse string JSON menjadi Dictionary Python
        gemini_data = json.loads(clean_text)
        print("✅ Berhasil parsing JSON dari Gemini.")

    except json.JSONDecodeError as e:
        print("❌ Gagal parsing output Gemini! Pastikan format prompt Gemini sudah benar.")
        print("Isi output mentah:\n", gemini_output_string)
        raise e

    # C. Hitung Skor Interview (Konversi Skala 4 ke 100)
    scores_list = gemini_data.get("scores", [])
    if not scores_list:
        print("⚠️ Peringatan: Tidak ada data 'scores' dalam output Gemini.")
        total_raw_score = 0
    else:
        total_raw_score = sum([item["score"] for item in scores_list])

    # Hitung Skor Maksimal: Jumlah Soal x Nilai Max per Soal (4)
    jumlah_soal = len(scores_list) if len(scores_list) > 0 else 1 # Hindari bagi nol
    max_possible = jumlah_soal * 4

    # Konversi ke skala 100
    interview_score_100 = (total_raw_score / max_possible) * 100

    # D. Hitung Total Akhir (Rata-rata Project & Interview)
    final_total = (review_meta["project"] + interview_score_100) / 2

    # ==========================================
    # 4. SUSUN JSON FINAL
    # ==========================================

    final_json = {
        "success": True,
        "data": {
            "candidate": candidate_info,
            "certification": cert_info,
            "reviewChecklists": {
                "project": [],
                # Membuat checklist dinamis dari ID soal yang dikembalikan Gemini
                "interviews": [
                    {"positionId": s["id"], "score": s["score"], "isVideoExist": True}
                    for s in scores_list
                ]
            },
            "reviewChecklistResult": {
                "project": [],
                "interviews": {
                    "minScore": 0,
                    "maxScore": 4,
                    "scores": scores_list, # Mengambil langsung array scores dari Gemini

                    # Mengambil nilai dinamis lain dari variabel output Gemini
                    # Menggunakan .get() agar tidak error jika field tidak ada
                    "communication_score": gemini_data.get("communication_score", 0),
                    "english_fluency_score": gemini_data.get("english_fluency_score", 0),
                    "content_quality_score": gemini_data.get("content_quality_score", 0)
                }
            },
            "scoresOverview": {
                "project": review_meta["project"],
                "interview_raw": total_raw_score,
                "interview_converted": round(interview_score_100, 2),
                "total": round(final_total, 2)
            },
            "assessorProfile": review_meta["assessorProfile"],
            "decision": review_meta["decision"],
            "reviewedAt": review_meta["reviewedAt"],
            "notes": review_meta["overall_notes"]
        }
    }
    return final_json