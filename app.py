from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import io
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ----------------------
# Config
# ----------------------
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"csv"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

DEFAULT_DATASET = 'III_DS-Student_Profiles.csv'
data_df = pd.read_csv(DEFAULT_DATASET)
data_df.columns = data_df.columns.str.strip()

# ----------------------
# Helpers
# ----------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ----------------------
# HackerRank Badges
# ----------------------
def fetch_hackerrank_badges_svg(username):
    try:
        badge_url = f'https://hackerrank-badges.vercel.app/{username}'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(badge_url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            badges = [t.get_text().strip() for t in soup.find_all('text') if len(t.get_text().strip()) > 1]
            return badges
    except Exception as e:
        print("Hackerrank fetch error:", e)
    return None

# ----------------------
# LeetCode Stats
# ----------------------
def fetch_leetcode_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("Leetcode fetch error:", e)
    return None

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return render_template('index.html')

# Upload dataset
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    global data_df
    if request.method == 'POST':
        if "file" not in request.files:
            return "No file part", 400
        file = request.files["file"]
        if file.filename == "":
            return "No selected file", 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            try:
                df = pd.read_csv(filepath)
                df.columns = df.columns.str.strip()
                data_df = df
                return "✅ Dataset uploaded and loaded successfully!"
            except Exception as e:
                return f"Error reading file: {str(e)}", 400
    return render_template("upload.html")

# Search individual student
@app.route('/student', methods=['POST'])
def student():
    roll = request.form.get('roll')
    if not roll:
        return "Roll number is required.", 400

    roll = roll.strip().upper()
    student = data_df[data_df['Roll Number'].str.upper() == roll]

    if not student.empty:
        data = student.iloc[0].to_dict()

        # LeetCode
        leetcode_url = data.get('Leet code links')
        if isinstance(leetcode_url, str) and 'leetcode.com' in leetcode_url:
            username = leetcode_url.rstrip('/').split('/')[-1]
            data['leetcode_stats'] = fetch_leetcode_data(username)

        # HackerRank
        hackerrank_url = data.get('Hackerrank profile link')
        if isinstance(hackerrank_url, str) and 'hackerrank.com' in hackerrank_url:
            username = hackerrank_url.rstrip('/').split('/')[-1]
            data['hackerrank_username'] = username
            data['hackerrank_badges'] = fetch_hackerrank_badges_svg(username)

        return render_template('student.html', data=data)

    return "Student not found."

# Bulk fetch all student data
@app.route('/bulk_fetch', methods=['GET','POST'])
def bulk_fetch():
    all_results = []
    for _, row in data_df.iterrows():
        roll = row.get("Roll Number", "")
        name = row.get("Name", "")
        leetcode_url = row.get("Leet code links", "")
        hackerrank_url = row.get("Hackerrank profile link", "")

        result = {"Roll Number": roll, "Name": name}

        # LeetCode
        if isinstance(leetcode_url, str) and 'leetcode.com' in leetcode_url:
            username = leetcode_url.rstrip('/').split('/')[-1]
            stats = fetch_leetcode_data(username)
            if stats:
                result.update({
                    "LeetCode Total Solved": stats.get("totalSolved"),
                    "LeetCode Easy": stats.get("easySolved"),
                    "LeetCode Medium": stats.get("mediumSolved"),
                    "LeetCode Hard": stats.get("hardSolved"),
                    "LeetCode Ranking": stats.get("ranking"),
                })

        # HackerRank
        if isinstance(hackerrank_url, str) and 'hackerrank.com' in hackerrank_url:
            username = hackerrank_url.rstrip('/').split('/')[-1]
            badges = fetch_hackerrank_badges_svg(username)
            result["HackerRank Badges"] = ", ".join(badges) if badges else "N/A"

        all_results.append(result)

    df = pd.DataFrame(all_results)

    # Export to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Profiles")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="student_profiles.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Optional JSON API
@app.route('/hackerrank_badges', methods=['POST'])
def hackerrank_badges():
    profile_url = request.form.get('hackerrank_url')
    if profile_url and 'hackerrank.com' in profile_url:
        username = profile_url.rstrip('/').split('/')[-1]
        badges = fetch_hackerrank_badges_svg(username)
        return jsonify(badges=badges)
    return jsonify({'error': 'Invalid URL'})

if __name__ == '__main__':
    app.run(debug=True)
