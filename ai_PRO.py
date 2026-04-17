import sqlite3
import random
import re

# ---------------- 1. DATABASE SETUP (Realistic Data & Weighted Marks) ----------------
def setup_database():
    """Initializes DB with realistic Indian names and performance-weighted marks."""
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

    # Unified list for parsing and generation
    student_names = ["Priya","Anu","Ravi","Kiran","Meena","Arjun","Sneha","Vikram","Divya","Rahul","Pooja","Nikhil","Suresh","Lakshmi","Varun","Keerthi","Ajay","Deepa","Manoj","Swathi","Ramesh","Anjali","Karthik","Bhavya","Harsha","Teja","Neha","Gopal","Sita","Madhu","Rohit","Asha","Krishna","Naveen","Sanjana","Tarun","Isha","Vinay","Preeti","Sai","Chandu","Prakash","Geetha","Mahesh","Radha","Vamsi","Shilpa","Aravind","Latha","Surya","Pavan","Nandini","Kishore","Rekha","Uday","Anitha","Yash","Mounika","Raj","Tejaswini","Lokesh","Sowmya","Abhi","Charan","Niharika","Dinesh","Ritu","Satish","Kavya","Om"]
    
    # Realistic Parent Names as requested (No more "Priya's Father")
    f_names = ["Sridhar", "Venkatesh", "Raghav", "Prabhakar", "Mohan", "Rajesh", "Srinivas", "Suryam", "Bhaskar", "Shankar", "Narayan", "Gopal"]
    m_names = ["Ganga", "Saraswathi", "Lakshmi", "Vani", "Savitri", "Roopa", "Anitha", "Kalyani", "Sunitha", "Parvathi", "Deepika", "Bhavani"]

    for name in student_names:
        age = random.randint(18, 22)
        # Random marks between 35 and 100 to make 'Pass/Fail' and 'Above 250' interesting
        m, p, c = random.randint(35, 100), random.randint(35, 100), random.randint(35, 100)
        father = random.choice(f_names)
        mother = random.choice(m_names)
        
        cursor.execute("""
            INSERT INTO students (name, class, age, math, phy, chem, father_name, mother_name) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
            (name, "3rd Year CSE", age, m, p, c, father, mother))

    conn.commit()
    conn.close()

# ---------------- 2. THE MASTER PARSER (Stateful + Priority Logic) ----------------
def process_query(user_input, session_prefs):
    user_input = user_input.lower().strip()
    
    # --- 2a. Update Persistent Session Memory ---
    if "always show details" in user_input or "full info" in user_input:
        session_prefs['mode'] = 'details'
        print(">> SYSTEM: 'Full Details' mode is now LOCKED for this session.")
    elif "show only names" in user_input and "father" not in user_input and "mother" not in user_input:
        session_prefs['mode'] = 'names'
        print(">> SYSTEM: Switched to 'Names Only' mode.")

    # --- 2b. Column Selection & "ONLY" Priority Logic ---
    # This section ensures specific requests override the "Always Show Details" lock
    if "only" in user_input:
        if "father" in user_input: select_clause = "name, father_name"
        elif "mother" in user_input: select_clause = "name, mother_name"
        elif "id" in user_input: select_clause = "id, name"
        else: select_clause = "name"
    elif session_prefs.get('mode') == 'details' or any(word in user_input for word in ["detail", "info", "full", "parent", "profile"]):
        select_clause = "*, (math + phy + chem) AS total_score"
    elif "score" in user_input or "mark" in user_input or "total" in user_input:
        select_clause = "name, (math + phy + chem) AS total_score"
    else:
        select_clause = "name"

    conditions = []

    # --- 2c. Specific Name Detection (Overwrites all filtering) ---
    names_list = ["priya","anu","ravi","kiran","meena","arjun","sneha","vikram","divya","rahul","pooja","nikhil","suresh","lakshmi","varun","keerthi","ajay","deepa","manoj","swathi","ramesh","anjali","karthik","bhavya","harsha","teja","neha","gopal","sita","madhu","rohit","asha","krishna","naveen","sanjana","tarun","isha","vinay","preeti","sai","chandu","prakash","geetha","mahesh","radha","vamsi","shilpa","aravind","latha","surya","pavan","nandini","kishore","reka","uday","anitha","yash","mounika","raj","tejaswini","lokesh","sowmya","abhi","charan","niharika","dinesh","ritu","satish","kavya","om"]
    for name in names_list:
        if re.search(rf'\b{name}\b', user_input):
            return f"SELECT *, (math + phy + chem) AS total_score FROM students WHERE name LIKE '{name}'"

    # --- 2d. Advanced Filtering Logic (Numbers & Keywords) ---
    val = 150 if "half" in user_input else (re.findall(r'\d+', user_input)[0] if re.findall(r'\d+', user_input) else None)

    # Regex for start/end letters
    start_m = re.search(r'start(?:ing)? with (?:letter\s+)?([a-z])', user_input)
    end_m = re.search(r'end(?:ing)? with (?:letter\s+)?([a-z])', user_input)
    if start_m: conditions.append(f"name LIKE '{start_m.group(1).upper()}%'")
    if end_m: conditions.append(f"name LIKE '%{end_m.group(1).lower()}'")

    # Comparisons
    target = "(math + phy + chem)"
    if "math" in user_input: target = "math"
    elif "phy" in user_input: target = "phy"
    elif "chem" in user_input: target = "chem"

    if val:
        if any(word in user_input for word in ["above", "greater", "more", ">"]):
            conditions.append(f"{target} > {val}")
        elif any(word in user_input for word in ["below", "less", "under", "<"]):
            conditions.append(f"{target} < {val}")

    # Pass/Fail Logic
    if "fail" in user_input or "failed" in user_input:
        conditions.append("(math < 40 OR phy < 40 OR chem < 40)")
    elif "pass" in user_input or "passed" in user_input:
        conditions.append("(math >= 40 AND phy >= 40 AND chem >= 40)")

    # --- 2e. Final SQL Assembly ---
    sql = f"SELECT {select_clause} FROM students"
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    return sql

# ---------------- 3. EXECUTION & DISPLAY ENGINE ----------------
def execute_and_display(sql):
    try:
        conn = sqlite3.connect("students.db")
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            print("\nResult: No matching records found for this criteria.")
            return

        print("\n" + "="*135)
        headers = rows[0].keys()
        print(" | ".join(f"{str(h).upper():^13}" for h in headers))
        print("-" * 135)
        for row in rows:
            print(" | ".join(f"{str(row[h]):^13}" for h in headers))
        print("="*135)
    except Exception as e:
        print(f"\nError in SQL Execution: {e}")

# ---------------- 4. MAIN PROGRAM ----------------
def main():
    setup_database()
    session_prefs = {'mode': 'names'} # Default starting mode
    print("--- CSE FINAL PROJECT: AI SQL ASSISTANT v6.0 ---")
    print("Commands: 'always show details', 'show only names', 'exit'")
    
    while True:
        query = input("\nEnter your query: ").strip()
        if query.lower() == 'exit': break
        if not query: continue

        generated_sql = process_query(query, session_prefs)
        print(f"DEBUG SQL: {generated_sql}") 
        
        execute_and_display(generated_sql)

if __name__ == "__main__":
    main()