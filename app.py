from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random
import re

app = Flask(__name__)
app.secret_key = "cse_secret_key_123"

# --- YOUR ORIGINAL LOGIC INTEGRATED ---

def setup_database():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS students")
    cursor.execute("""
    CREATE TABLE students (
        id INTEGER PRIMARY KEY,
        name TEXT, class TEXT, age INTEGER,
        math INTEGER, phy INTEGER, chem INTEGER,
        father_name TEXT, mother_name TEXT
    )
    """)
    student_names = ["Priya","Anu","Ravi","Kiran","Meena","Arjun","Sneha","Vikram","Divya","Rahul","Pooja","Nikhil","Suresh","Lakshmi","Varun","Keerthi","Ajay","Deepa","Manoj","Swathi","Ramesh","Anjali","Karthik","Bhavya","Harsha","Teja","Neha","Gopal","Sita","Madhu","Rohit","Asha","Krishna","Naveen","Sanjana","Tarun","Isha","Vinay","Preeti","Sai","Chandu","Prakash","Geetha","Mahesh","Radha","Vamsi","Shilpa","Aravind","Latha","Surya","Pavan","Nandini","Kishore","Rekha","Uday","Anitha","Yash","Mounika","Raj","Tejaswini","Lokesh","Sowmya","Abhi","Charan","Niharika","Dinesh","Ritu","Satish","Kavya","Om"]
    f_names = ["Sridhar", "Venkatesh", "Raghav", "Prabhakar", "Mohan", "Rajesh", "Srinivas", "Suryam", "Bhaskar", "Shankar", "Narayan", "Gopal"]
    m_names = ["Ganga", "Saraswathi", "Lakshmi", "Vani", "Savitri", "Roopa", "Anitha", "Kalyani", "Sunitha", "Parvathi", "Deepika", "Bhavani"]

    for name in student_names:
        m, p, c = random.randint(35, 100), random.randint(35, 100), random.randint(35, 100)
        cursor.execute("INSERT INTO students (name, class, age, math, phy, chem, father_name, mother_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                       (name, "3rd Year CSE", random.randint(18, 22), m, p, c, random.choice(f_names), random.choice(m_names)))
    conn.commit()
    conn.close()

def process_query(user_input, session_prefs):
    user_input = user_input.lower().strip()
    if "always show details" in user_input or "full info" in user_input:
        session_prefs['mode'] = 'details'
    elif "show only names" in user_input and "father" not in user_input and "mother" not in user_input:
        session_prefs['mode'] = 'names'

    if "only" in user_input:
        if "father" in user_input: select_clause = "name, father_name"
        elif "mother" in user_input: select_clause = "name, mother_name"
        else: select_clause = "name"
    elif session_prefs.get('mode') == 'details' or any(word in user_input for word in ["detail", "info", "full", "parent"]):
        select_clause = "*, (math + phy + chem) AS total_score"
    else:
        select_clause = "name"

    conditions = []
    names_list = ["priya","anu","ravi","kiran","meena","arjun","sneha","vikram","divya","rahul","pooja","nikhil","suresh","lakshmi","varun","keerthi","ajay","deepa","manoj","swathi","ramesh","anjali","karthik","bhavya","harsha","teja","neha","gopal","sita","madhu","rohit","asha","krishna","naveen","sanjana","tarun","isha","vinay","preeti","sai","chandu","prakash","geetha","mahesh","radha","vamsi","shilpa","aravind","latha","surya","pavan","nandini","kishore","reka","uday","anitha","yash","mounika","raj","tejaswini","lokesh","sowmya","abhi","charan","niharika","dinesh","ritu","satish","kavya","om"]
    for name in names_list:
        if re.search(rf'\b{name}\b', user_input):
            return f"SELECT *, (math + phy + chem) AS total_score FROM students WHERE name LIKE '{name}'"

    val = 150 if "half" in user_input else (re.findall(r'\d+', user_input)[0] if re.findall(r'\d+', user_input) else None)
    start_m = re.search(r'start(?:ing)? with (?:letter\s+)?([a-z])', user_input)
    end_m = re.search(r'end(?:ing)? with (?:letter\s+)?([a-z])', user_input)
    if start_m: conditions.append(f"name LIKE '{start_m.group(1).upper()}%'")
    if end_m: conditions.append(f"name LIKE '%{end_m.group(1).lower()}'")

    target = "(math + phy + chem)"
    if "math" in user_input: target = "math"
    elif "phy" in user_input: target = "phy"
    elif "chem" in user_input: target = "chem"

    if val:
        if any(word in user_input for word in ["above", "greater", "more", ">"]): conditions.append(f"{target} > {val}")
        elif any(word in user_input for word in ["below", "less", "under", "<"]): conditions.append(f"{target} < {val}")

    if "fail" in user_input: conditions.append("(math < 40 OR phy < 40 OR chem < 40)")
    elif "pass" in user_input: conditions.append("(math >= 40 AND phy >= 40 AND chem >= 40)")

    sql = f"SELECT {select_clause} FROM students"
    if conditions: sql += " WHERE " + " AND ".join(conditions)
    return sql

# --- WEB ROUTES ---

@app.route('/')
def index():
    setup_database()
    session['mode'] = 'names'
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query')
    session_prefs = {'mode': session.get('mode', 'names')}
    sql = process_query(query, session_prefs)
    session['mode'] = session_prefs['mode'] # Persistent memory

    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return jsonify({"data": result, "sql": sql})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)