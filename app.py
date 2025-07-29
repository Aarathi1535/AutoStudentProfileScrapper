from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

data_df = pd.read_csv('III_DS-Student_Profiles.csv')
data_df.columns = data_df.columns.str.strip()

def fetch_hackerrank_badges_svg(username):
    VALID_HACKERRANK_BADGES = {
        'Problem Solving', 'Java', 'Python', 'C Language', 'Cpp', 'C#', 'JavaScript',
        'Sql', '30 Days of Code', '10 Days of JavaScript', '10 Days of Statistics',
        'Algorithms', 'Data Structures', 'Regex', 'Artificial Intelligence',
        'Databases', 'Shell', 'Linux Shell', 'Functional Programming',
        'Mathematics', 'Days of ML', 'Rust', 'Kotlin', 'Swift', 'Scala',
        'Ruby', 'Go', 'Statistics', 'Interview Preparation Kit',
        'Object Oriented Programming', 'Linux Shell', 'Security'
    }

    try:
        badge_url = f'https://hackerrank-badges.vercel.app/{username}'
        response = requests.get(badge_url, timeout=15)

        if response.status_code == 200:
            svg_xml = response.text
            soup = BeautifulSoup(svg_xml, 'xml')
            text_elements = soup.find_all('text')
            star_sections = soup.find_all('g', class_='star-section')

            badge_keywords = ['java', 'python', 'sql', 'javascript', 'cpp', 'problem solving', 
                              'algorithms', 'data structures', '30 days', '10 days', 'ruby', 
                              'swift', 'golang', 'rust', 'kotlin', 'scala', 'c', 'shell',
                              'functional programming', 'object oriented programming']

            all_texts = [t.get_text().strip() for t in text_elements if len(t.get_text().strip()) > 1]
            real_badges = []

            for text in all_texts:
                text_lower = text.lower()
                for keyword in badge_keywords:
                    if keyword in text_lower:
                        text_title = text.strip().title()
                        if text_title not in VALID_HACKERRANK_BADGES:
                            continue

                        stars = 0
                        for star_section in star_sections:
                            if star_section.find('text') and star_section.find('text').get_text().strip().lower() == text_lower:
                                stars = len(star_section.find_all('svg', class_='badge-star'))
                                break

                        real_badges.append({'Badge Name': text_title, 'Stars': stars})
                        break

            seen = set()
            unique_badges = [b for b in real_badges if not (b['Badge Name'].lower() in seen or seen.add(b['Badge Name'].lower()))]
            return unique_badges if unique_badges else None
        else:
            return None
    except:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/student', methods=['POST'])
def student():
    roll = request.form.get('roll').strip().upper()
    student = data_df[data_df['Roll Number'].str.upper() == roll]
    if not student.empty:
        data = student.iloc[0].to_dict()
        return render_template('student.html', data=data)
    return "Student not found."

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
