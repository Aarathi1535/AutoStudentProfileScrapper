from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import json

app = Flask(__name__)

# Load dataset
data_df = pd.read_csv('III_DS-Student_Profiles.csv')
data_df.columns = data_df.columns.str.strip()


# ----------------------
# HackerRank Badges Logic
# ----------------------
def fetch_hackerrank_badges_svg(username):
    print(f"🔍 Fetching badges for username: {username}")

    """
    Fetch HackerRank badges by parsing SVG structure directly
    Returns list of dictionaries with badge names and star counts
    """
    # Predefined list of valid HackerRank badges
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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(badge_url, headers=headers, timeout=15)


        if response.status_code == 200:
            print("📥 Successfully fetched badge SVG.")
            svg_xml = response.text
            soup = BeautifulSoup(svg_xml, 'xml')
            
            # Debug info
            
            # Look for badge information in the SVG
            text_elements = soup.find_all('text')
            
            # Look for star sections - this is the key structure
            star_sections = soup.find_all('g', class_='star-section')
            
            # Look for individual badge stars
            badge_stars = soup.find_all('svg', class_='badge-star')
            
            # Display all text content to understand the structure
            all_texts = []
            for text in text_elements:
                text_content = text.get_text().strip()
                if text_content and len(text_content) > 1:
                    all_texts.append(text_content)
            
            
            
            # Analyze star sections
            for i, star_section in enumerate(star_sections):
                stars_in_section = star_section.find_all('svg', class_='badge-star')
            
            # Try to identify actual badges by looking for meaningful patterns
            badge_keywords = ['java', 'python', 'sql', 'javascript', 'cpp', 'problem solving', 
                            'algorithms', 'data structures', '30 days', '10 days', 'ruby', 
                            'swift', 'golang', 'rust', 'kotlin', 'scala', 'c', 'shell',
                            'functional programming', 'object oriented programming']
            
            real_badges = []
            
            # Strategy: Match badges with their corresponding star sections
            # The structure seems to be: badge text + associated star-section
            for text in all_texts:
                text_lower = text.lower()
                for keyword in badge_keywords:
                    if keyword in text_lower:
                        
                        # ✅ Check if badge is in VALID_HACKERRANK_BADGES
                        text_title = text.strip().title()
                        if text_title not in VALID_HACKERRANK_BADGES:
                            continue  # Skip if not a valid badge name
                        
                        # Find the text element in the soup
                        text_elem = None
                        for elem in text_elements:
                            if elem.get_text().strip().lower() == text_lower:
                                text_elem = elem
                                break

                        
                        stars = 0
                        if text_elem:
                            # Strategy 1: Look for star-section in the same parent or nearby elements
                            # Traverse up the DOM tree to find associated star sections
                            current = text_elem
                            found_stars = False
                            
                            # Check multiple levels up the DOM tree
                            for level in range(5):  # Check up to 5 levels up
                                if current is None:
                                    break
                                    
                                # Look for star-section in current element
                                star_section = current.find('g', class_='star-section')
                                if star_section:
                                    badge_star_elements = star_section.find_all('svg', class_='badge-star')
                                    stars = len(badge_star_elements)
                                    found_stars = True
                                    break
                                
                                # Look for star-section in siblings
                                if current.parent:
                                    sibling_star_sections = current.parent.find_all('g', class_='star-section')
                                    if sibling_star_sections:
                                        # Take the first star section found (assuming it's related)
                                        badge_star_elements = sibling_star_sections[0].find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        break
                                
                                current = current.parent
                            
                            # Strategy 2: If no direct association found, try positional matching
                            if not found_stars and star_sections:
                                
                                # Get text position
                                text_x = text_elem.get('x', '0')
                                text_y = text_elem.get('y', '0')
                                
                                try:
                                    text_x_num = float(text_x) if str(text_x).replace('.', '').replace('-', '').isdigit() else 0
                                    text_y_num = float(text_y) if str(text_y).replace('.', '').replace('-', '').isdigit() else 0
                                    
                                    closest_star_section = None
                                    min_distance = float('inf')
                                    
                                    for star_section in star_sections:
                                        # Get star section position from transform attribute
                                        transform = star_section.get('transform', '')
                                        if 'translate' in transform:
                                            # Extract translate values
                                            import re
                                            translate_match = re.search(r'translate\(([^,]+),\s*([^)]+)\)', transform)
                                            if translate_match:
                                                try:
                                                    star_x = float(translate_match.group(1))
                                                    star_y = float(translate_match.group(2))
                                                    
                                                    distance = ((star_x - text_x_num) ** 2 + (star_y - text_y_num) ** 2) ** 0.5
                                                    if distance < min_distance:
                                                        min_distance = distance
                                                        closest_star_section = star_section
                                                except:
                                                    continue
                                    
                                    if closest_star_section:
                                        badge_star_elements = closest_star_section.find_all('svg', class_='badge-star')
                                        stars = len(badge_star_elements)
                                        found_stars = True
                                        
                                except:
                                    pass
                            
                            # Strategy 3: Simple distribution if we have star sections
                            if not found_stars and star_sections:
                                print("  📊 Using simple distribution strategy...")
                                # Count total stars and distribute among badges
                                total_star_elements = soup.find_all('svg', class_='badge-star')
                                total_badges = len([t for t in all_texts if any(kw in t.lower() for kw in badge_keywords)])
                                if total_badges > 0:
                                    stars = len(total_star_elements) // total_badges
                                    print(f"  ⭐ Estimated {stars} stars ({len(total_star_elements)} total / {total_badges} badges)")
                        
                        real_badges.append({
                            'Badge Name': text.title(),
                            'Stars': stars
                        })
                        
                        break  # Found this badge, don't check other keywords
            
            # Remove duplicates
            seen = set()
            unique_badges = []
            for badge in real_badges:
                badge_key = badge['Badge Name'].lower()
                if badge_key not in seen:
                    seen.add(badge_key)
                    unique_badges.append(badge)
            
            
            
            return unique_badges if unique_badges else None
            
        else:
            print(f"HTTP Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None




# ----------------------
# LeetCode Stats Logic
# ----------------------
def fetch_leetcode_data(username):
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None


# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/student', methods=['POST'])
def student():
    roll = request.form.get('roll')
    if not roll:
        return "Roll number is required.", 400

    roll = roll.strip().upper()
    student = data_df[data_df['Roll Number'].str.upper() == roll]

    if not student.empty:
        data = student.iloc[0].to_dict()

        # ---------- LeetCode ----------
        leetcode_url = data.get('Leet code links')
        leetcode_stats = None
        if isinstance(leetcode_url, str) and 'leetcode.com' in leetcode_url:
            username = leetcode_url.rstrip('/').split('/')[-1]
            leetcode_stats = fetch_leetcode_data(username)
            data['leetcode_stats'] = leetcode_stats

        # ---------- HackerRank ----------
        hackerrank_url = data.get('Hackerrank profile link')
        hackerrank_badges = None
        if isinstance(hackerrank_url, str) and 'hackerrank.com' in hackerrank_url:
            username = hackerrank_url.rstrip('/').split('/')[-1]
            data['hackerrank_username'] = username
            hackerrank_badges = fetch_hackerrank_badges_svg(username)
            data['hackerrank_badges'] = hackerrank_badges

        return render_template('student.html', data=data)

    return "Student not found."


# Optional route if you're using JSON fetch externally
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
