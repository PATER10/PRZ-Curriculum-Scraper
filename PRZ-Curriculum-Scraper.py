import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import uuid

# ==========================================================
# 1. CONFIGURATION AND ID MAPS
# ==========================================================
from ID_MAPS import FACULTY_MAP, DIRECTION_MAP, SPECIALIZATION_MAP
# FACULTY_MAP = {
#     "weii": "uuid"
# }

# --- List of colors for subjects ---
SUBJECT_COLORS = [
    '#003366', '#1a6b3a', '#7c3aed', '#b45309', '#0369a1', '#be123c',
    '#1e293b', '#065f46', '#991b1b', '#5b21b6', '#92400e', '#075985',
    '#4d7c0f', '#a21caf', '#115e59', '#c2410c', '#3730a3', '#854d0e',
    '#155e75', '#9f1239', '#3f6212', '#6b21a8', '#0369a1', '#b91c1c',
    '#0e7490', '#525252'
]

# ==========================================================
# 2. FUNTIONS
# ==========================================================
def fetch_topics_for_subject(mk_id, subject_id, year=2024, lang='EN'):
    """Accesses the subject card, fetches curriculum topics (TK), and links them to subject_id"""
    url = f"https://krk.prz.edu.pl/karta.pl?mk={mk_id}&format=v1_html&C={year}&lng={lang}"
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    knowledge_points = []
    tables = soup.find_all('table')
    
    for table in tables:
        # Check for 'TK' and header text in both English and Polish
        if 'TK' in table.text and ('The content' in table.text or 'Treści programowe' in table.text):
            rows = table.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) >= 3:
                    tk_code = columns[1].text.strip()
                    if tk_code.startswith('TK'):
                        raw_content = columns[2].text.strip()
                        content = " ".join(raw_content.split())
                        
                        try:
                            order_num = int(tk_code.replace('TK', ''))
                        except ValueError:
                            order_num = 99
                        
                        knowledge_points.append({
                            'id': str(uuid.uuid4()), 
                            'subject_id': subject_id, 
                            'order': order_num,
                            'description': content,
                            'estimated_minutes': 60
                        })
            break
            
    return knowledge_points

def scrape_full_curriculum(url, faculty_id, direction_id, specialization_id=None, start_sem=1, end_sem=4):
    """Main function: fetches subjects and immediately scrapes their topics"""
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    
    target_table = soup.find('table', class_='analiza')
    if not target_table:
        print("ERROR: Study plan table not found!")
        return [], []

    subjects = []
    all_knowledge_points = []
    
    # Dictionary to track the number of subjects in a given semester
    semester_counters = {}
    
    rows = target_table.find_all('tr')
    
    for row in rows:
        cols = row.find_all('td')
        if len(cols) < 11: continue
            
        try:
            semester_text = cols[0].text.strip()
            if not semester_text.isdigit(): continue
            semester = int(semester_text)
            
            if semester < start_sem or semester > end_sem:
                continue
            
            module_cell = cols[2]
            name = module_cell.text.strip()
            if not name: continue
            
            # Default search for mk_id on the page
            link = module_cell.find('a')
            mk_id = None
            if link and 'href' in link.attrs:
                match = re.search(r'mk=(\d+)', link['href'])
                if match: mk_id = int(match.group(1))
            
            # EXCEPTION HANDLING (Languages and Elective Modules)
            if "Foreign language" in name or "Język obcy" in name:
                mk_id = None #ENGLISH_MK_ID
                print(f"  -> Could not fetch info for foreign language or default assigned (mk_id: {mk_id}) for semester {semester}")
            
            if "Chosen module" in name or "Przedmiot wybieralny" in name:
                mk_id = None
                print(f"  -> Skipping topics for elective block: {name}")

            exam_text = cols[9].text.strip()
            has_exam = True if exam_text == 'Y' else False
            
            # ======================================================
            # COLOR ASSIGNMENT LOGIC
            # ======================================================
            if semester not in semester_counters:
                semester_counters[semester] = 0
            
            # Get color based on counter (modulo prevents index out of bounds)
            color_index = semester_counters[semester] % len(SUBJECT_COLORS)
            assigned_color = SUBJECT_COLORS[color_index]
            
            # Increment counter for this semester
            semester_counters[semester] += 1
            # ======================================================
            
            subject_id = str(uuid.uuid4())
            
            subject = {
                'id': subject_id,
                'faculty_id': faculty_id,
                'direction_id': direction_id,
                'specialization_id': specialization_id,
                'semester': semester,
                'name': name,
                'has_exam': has_exam,
                'exam_date': None,
                'color': assigned_color
            }
            subjects.append(subject)
            
            if mk_id:
                print(f"Fetching topics: Sem {semester} | {name} (Color: {assigned_color})")
                kps = fetch_topics_for_subject(mk_id, subject_id)
                all_knowledge_points.extend(kps)
            else:
                print(f"No subpage/topics for: Sem {semester} | {name} (Color: {assigned_color})")
                
        except Exception as e:
            print(f"Error processing row: {e}")
            continue
            
    return subjects, all_knowledge_points

def export_data(subjects, knowledge_points, prefix):
    """Saves data to CSV and JSON"""
    if subjects:
        df_sub = pd.DataFrame(subjects)
        df_sub.to_csv(f'{prefix}_subjects.csv', index=False, encoding='utf-8')
        with open(f'{prefix}_subjects.json', 'w', encoding='utf-8') as f:
            json.dump(subjects, f, ensure_ascii=False, indent=4)
            
    if knowledge_points:
        df_kp = pd.DataFrame(knowledge_points)
        df_kp.to_csv(f'{prefix}_knowledge_points.csv', index=False, encoding='utf-8')
        with open(f'{prefix}_knowledge_points.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge_points, f, ensure_ascii=False, indent=4)
            
    print(f"Files saved with prefix: {prefix} ({len(subjects)} subjects, {len(knowledge_points)} topics)")

# ==========================================================
# 3. SCRIPT EXECUTION
# ==========================================================
if __name__ == "__main__":
    URL_BASE = "https://krk.prz.edu.pl/plany.pl?lng=EN&W=E&K=E&KW=&TK=html&S=299&P=&C=2024&erasmus=&O="
    URL_SPEC = "https://krk.prz.edu.pl/plany.pl?lng=EN&W=E&K=E&KW=&TK=html&S=300&P=&C=2024&erasmus=&O="

    real_faculty_id = FACULTY_MAP["weii"]
    real_direction_id = DIRECTION_MAP["weii-ee"]
    real_specialization_id = SPECIALIZATION_MAP["weii-ee-Odnawialne źródła energii i technika świetlna"]

    print(" STARTING DOWNLOAD: BASE (SEMESTERS 1-4)")
    base_subjects, base_kps = scrape_full_curriculum(
        url=URL_BASE,
        faculty_id=real_faculty_id,
        direction_id=real_direction_id,
        specialization_id=None,
        start_sem=1,
        end_sem=4
    )
    export_data(base_subjects, base_kps, "sem1_4_base")
    
    print("\n \n STARTING DOWNLOAD: SPECIALIZATION (SEMESTERS 5-7)")
    spec_subjects, spec_kps = scrape_full_curriculum(
        url=URL_SPEC,
        faculty_id=real_faculty_id,
        direction_id=real_direction_id,
        specialization_id=real_specialization_id,
        start_sem=5,
        end_sem=7
    )
    export_data(spec_subjects, spec_kps, "sem5_7_spec_Odnawialne źródła energii i technika świetlna")
    
    print("\n COMPLETED SUCCESSFULLY!")