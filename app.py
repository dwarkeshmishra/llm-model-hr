from flask import Flask, render_template, request, jsonify
import os
import pdfminer
import docx2txt
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from transformers import pipeline  # Add this import

app = Flask(__name__)

def parse_cv(file):
    """Parses a CV file and returns its text."""
    if file.filename.endswith('.pdf'):
        return pdfminer.parse_pdf(file)
    elif file.filename.endswith('.docx'):
        return docx2txt.process(file)
    else:
        return ""

def get_matched_skills(job_description, cv):
    """Gets the matched skills between a job description and a CV."""
    nlp = pipeline("fill-mask")  # Load the language model pipeline
    skills = nlp(job_description)
    matched_skills = [skill["token_str"] for skill in skills]
    matched_skills = [skill for skill in matched_skills if skill in cv]
    return matched_skills

def get_cv_score(job_description, cv):
    """Gets the CV score for a CV."""
    matched_skills = get_matched_skills(job_description, cv)
    experience = len(cv.split('.'))
    return len(matched_skills) * 10 + experience

def send_email(subject, message, recipient):
    """Sends an email to a recipient."""
    sender_email = "your_email@example.com"  # Your email
    sender_password = "your_password"  # Your email password

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error sending email:", str(e))
        return False

@app.route("/apply", methods=["POST"])
def apply():
    """Handles job application requests."""
    job_title = request.form["job-title"]
    job_description = request.form["job-description"]
    cv = request.files["cv"]

    cv_text = parse_cv(cv)
    matched_skills = get_matched_skills(job_description, cv_text)
    cv_score = get_cv_score(job_description, cv_text)

    candidate = {
        "name": request.form["name"],
        "job_title": job_title,
        "cv_score": cv_score,
        "matched_skills": matched_skills,
        "experience": len(cv_text.split('.')),
        "email": request.form["email"],  # Adding email to candidate data
    }

    with open("candidates.json", "a") as f:
        json.dump(candidate, f)
        f.write('\n')

    email_subject = "Application Received"
    email_message = f"Thank you for applying for the {job_title} position."
    send_email(email_subject, email_message, request.form["email"])

    return jsonify(candidate)

@app.route("/shortlisted-candidates")
def shortlisted_candidates():
    """Gets the shortlisted candidates from the dataset."""
    with open("candidates.json", "r") as f:
        candidates = [json.loads(line) for line in f]

    return render_template("hr.html", candidates=candidates)

if __name__ == "__main__":
    app.run(debug=True)
app.url_map.strict_slashes = False
app.debug = True
