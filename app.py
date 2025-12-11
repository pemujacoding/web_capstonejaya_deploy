from flask import Flask, render_template, request, redirect, url_for, flash, session
import model.users as conn_users
import model.interview as conn_interview
import model.candidates as conn_candidates
import model.final_result as conn_final
import os
import json
import processing.input_process as p_input
import processing.gemini as g_input
import tempfile

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_i_am_fixing_my_app'

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user_id = conn_users.check_user(username,password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            return redirect(url_for("homepage"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        fullname = request.form.get("fullname")
        email = request.form.get("email")

        try:
            conn_users.create_user(username,password,fullname,email)
            
            flash(f"Account for {username} created successfully! Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            print(f"Error creating user: {e}")
            flash("Could not create account. Username might already exist.", "error")
            return render_template("signin.html")

    return render_template("signin.html")

@app.route("/dashboard/", methods=["GET", "POST"])

@app.route("/dashboard/homepage", methods=["GET", "POST"])
def homepage():
    if 'user_id' not in session:
        flash("Please log in to view the dashboard.", "error")
        return redirect(url_for('login'))
    username = session.get('username', 'Guest')
    return render_template("homepage.html",username=username)

@app.route('/logout')
def logout():
    # Remove the user_id and username from the session
    session.pop('user_id', None)
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route("/dashboard/history", methods=["GET", "POST"])
def history():
    if 'user_id' not in session:
        flash("Please log in to view the dashboard.", "error")
        return redirect(url_for('login'))
    user_id = session.get('user_id', 'Guest_id')
    interview_list = conn_interview.get_history(user_id)
    return render_template("history.html",interview_list=interview_list)

@app.route("/dashboard/candidates", methods=["GET", "POST"])
def candidates():
    if 'user_id' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login'))
    candidates = conn_candidates.get_candidates()
    return render_template('candidates.html',candidates = candidates)

@app.route("/dashboard/add_candidates", methods=["GET", "POST"])
def add_candidates():
    if 'user_id' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login'))
    
    if request.method == "POST" :
        name = request.form.get("name")
        email = request.form.get("email")
        photo = request.form.get("photo")
        try:
            conn_candidates.insert(name,email,photo)
            
            flash(f"Candidate {name} succesfully added", "success")
            return redirect(url_for("candidates"))

        except Exception as e:
            flash("Could not add candidate", "error")
            return render_template("add_candidate.html")
    return render_template('add_candidates.html')

@app.route("/dashboard/edit_candidate/<int:candidate_id>", methods=["GET", "POST"])
def edit_candidate(candidate_id):
    candidate = conn_candidates.get_by_id(candidate_id)
    if not candidate:
        flash("Candidate not found!", "error")
        return redirect(url_for("candidates"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        photoUrl = request.form.get("photoUrl")

        if not name or not email:
            flash("Name and email are required!", "error")
            return redirect(request.url)
        
        try :
            conn_candidates.update(candidate_id, name, email, photoUrl)
            flash("Candidate updated successfully!", "success")
            return redirect(url_for("candidates"))
        except :
            flash("Update failed", "danger")
    return render_template("edit_candidate.html", candidate=candidate)

@app.route("/dashboard/delete_candidate/<int:candidate_id>", methods=["GET","POST"])
def delete_candidate(candidate_id):
    candidate = conn_candidates.get_by_id(candidate_id)
    if not candidate:
        flash("Candidate not found!", "error")
        return redirect(url_for("candidates"))

    conn_candidates.delete(candidate_id)
    flash("Candidate deleted successfully!", "success")
    return redirect(url_for("candidates"))

@app.route("/dashboard/final_result/<int:interview_id>", methods=["GET", "POST"])
def final_result(interview_id):
    if 'user_id' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login'))
    user_id = session.get('user_id', 'Guest_id')
    interview = conn_interview.get_for_final(user_id,interview_id)
    final = conn_final.get_by_id(interview_id)

    if request.method == "POST" :
        project = request.form.get("project")
        
    if not interview:
        flash("Interview not found.", "error")
        return redirect(url_for("history"))
    return render_template("final_result.html",interview=interview,final=final)

@app.route("/dashboard/delete_interview/<int:interview_id>", methods=["GET","POST"])
def delete_interview(interview_id):
    interview = conn_interview.get_by_id(interview_id)
    if not interview:
        flash("Candidate not found!", "error")
        return redirect(url_for("history"))
    conn_interview.delete_interview(interview_id)
    flash("Interview deleted successfully!", "success")
    return redirect(url_for("history"))

@app.route("/dashboard/new_interview", methods=["GET", "POST"])
def new_interview():
    if 'user_id' not in session:
        flash("Please log in to view this page.", "error")
        return redirect(url_for('login'))

    candidates = conn_candidates.get_candidates()
   
    if request.method == "POST":
        user_id = session.get("user_id")
        candidate_id = request.form.get("candidate_id")

        # Ambil list pertanyaan & list video (dinamis)
        questions = request.form.getlist("questions[]")
        videos = request.files.getlist("videos[]")

        # Validasi
        if not candidate_id:
            flash("Please select a candidate.", "error")
            return redirect(request.url)

        if len(questions) == 0 or len(videos) == 0:
            flash("Please add at least 1 question and 1 video.", "error")
            return redirect(request.url)

        if len(questions) != len(videos):
            flash("Number of questions and videos must match.", "error")
            return redirect(request.url)

        # Buat session interview baru
        session_id = conn_interview.insert_new_interview_session(user_id, candidate_id)

        all_results_cd = []
        all_results_stt = []

        # Loop semua input dinamis
        for idx, (q, file) in enumerate(zip(questions, videos), start=1):
            if file.filename == "":
                flash(f"Missing video for Question {idx}.", "error")
                return redirect(request.url)

            filename, ext = os.path.splitext(file.filename)
            ext = ext.lower()
            if ext not in ['.mp4', '.webm']:
                flash(f"Invalid file extension for Question {idx}. Only MP4 and WebM allowed.", "error")
                return redirect(request.url)

            # Simpan file sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                file.save(tmp.name)
                temp_path = tmp.name

            try:
                # Proses video (YOLO + STT)
                result_cd, result_stt = p_input.input_files(
                    temp_path, filename, ext, session_id, q
                )

                if result_cd and result_stt:
                    all_results_cd.append(result_cd)
                    all_results_stt.append(result_stt)
                else:
                    flash(f"Processing failed for Question {idx}.", "error")
                    return redirect(request.url)

            finally:
                os.remove(temp_path)

        # ----- GEMINI PROCESSING -----
        try :
            gemini_result = g_input.gemini_analyze(all_results_stt)
            gemini_result_clean = gemini_result.strip() if gemini_result else None
            int_status = "Success"
        except :
            int_status="Troubled"

        conn_interview.update_interview(gemini_result_clean, session_id)

        flash("Interview processed successfully!", int_status)
        return redirect(url_for('history'))

    return render_template("interview.html", candidates = candidates)


if __name__ == "__main__":
    app.run(debug=True)
