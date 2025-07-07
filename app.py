import logging
logging.basicConfig(level=logging.INFO)
logging.info("app.py start")

import streamlit as st
logging.info("Streamlit imported")

from gdrive_utils import get_drive_service
logging.info("gdrive_utils imported")

from parse_query import parse_query, semantic_ranking
logging.info("parse_query imported")










import streamlit as st
from gdrive_utils import get_drive_service, list_pdf_metadata, file_link
from parse_query import parse_query, semantic_ranking
import re

# 🎨 Streamlit page setup
st.set_page_config(page_title="📘 PYQ Chatbot", layout="wide")
st.markdown("""
    <h1 style="color:#3366cc;">📘 Previous Year Question Paper Chatbot</h1>
    <p style="font-size:18px;">🔍 Find question papers by subject, course, semester, year, or paper number — instantly!</p>
    <hr>
""", unsafe_allow_html=True)

# 📁 Google Drive root folder ID
folder_id = "1u14E3LRMkKlASQF-sjtkDrefjtq5ZWq9"  # Replace with your actual ID

# Step 1: Welcome Screen and Initial Prompt
st.write("Welcome! 👋 Do you want to view or download Previous Year Question Papers (PYQs)?")
proceed = st.radio("Choose your action:", ('Yes, I want to see PYQs!', 'No, maybe later.'))

if proceed == 'Yes, I want to see PYQs!':
    # Step 2: Gather user's preferences
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("Enter the year:", min_value=2000, max_value=2100, step=1)
    with col2:
        subject = st.selectbox("Select the subject:", [
            "Bengali", "Botany", "Chemistry", "Commerce", "Computer Science", "Economics",
            "Education", "Electronics", "English", "ENVS", "Film Studies", "History",
            "Journalism", "Mathematics", "Philosophy", "Physics", "Pol Science", "Zoology"
        ])
    with col3:
        course = st.selectbox("Select the course type:", ["Hons", "Gen"])

    col4, col5 = st.columns(2)
    with col4:
        semester = st.selectbox("Select the semester:", [1, 2, 3, 4, 5, 6])
    with col5:
        paper_num = st.selectbox("Select paper number (optional):",
                                 ["All papers"] + [f"Paper {i}" for i in range(1, 11)],
                                 index=0)

    # Step 3: Perform Search
    if st.button("Search PYQs"):
        paper_pattern = ""
        if paper_num != "All papers":
            paper_index = int(paper_num.split(" ")[1])
            paper_pattern = f"{course[0].lower()}" + ("" if paper_index == 1 else f"-{paper_index}")

        query = f"{subject} {course} semester {semester} {year}"
        parsed = parse_query(query)

        try:
            service = get_drive_service()
            raw_meta = list_pdf_metadata(service, folder_id, year)

            if not raw_meta:
                st.warning("❌ No PDFs found for the specified year.")
                st.stop()

            meta = []
            for m in raw_meta:
                sem_match = re.search(r'(\d+)', m["semester_folder"])
                m["sem"] = int(sem_match.group(1)) if sem_match else None

                pattern = rf'([^a-zA-Z]{course[0].lower()}(?:-(\d+))?[^a-zA-Z])'
                paper_match = re.search(pattern, m["name"], re.IGNORECASE)

                if paper_match:
                    paper_num_str = paper_match.group(2)
                    m["paper_num"] = int(paper_num_str) if paper_num_str else 1
                    m["paper_pattern"] = f"{course[0].lower()}-{paper_num_str}" if paper_num_str else course[0].lower()
                else:
                    m["paper_num"] = 1
                    m["paper_pattern"] = course[0].lower()

                meta.append(m)

            st.success(f"✅ Loaded {len(meta)} PDFs from Drive.")
            ranked = semantic_ranking(query, meta, top_k=20)

            filtered = []
            for m in ranked:
                if parsed["subject"] and parsed["subject"].lower() not in m["subject"].lower():
                    continue
                if parsed["course"] and parsed["course"].lower() not in m["course"].lower():
                    continue
                if parsed["sem"] and parsed["sem"] != m.get("sem"):
                    continue
                if paper_pattern and m["paper_pattern"].lower() != paper_pattern.lower():
                    continue
                filtered.append(m)

            if not filtered:
                st.warning("❌ No matching question papers found.")
                st.info(f"Debug info: Year={year}, Subject={subject}, Course={course}, Semester={semester}, Paper={paper_pattern}")
                st.info(f"Top ranked PDF names: {[m['name'] for m in ranked[:5]]}")
            else:
                st.success(f"✅ Found {len(filtered)} matching papers:")
                for m in filtered:
                    file_id = m["id"]
                    download_url = file_link(file_id)
                    preview_url = f"https://drive.google.com/file/d/{file_id}/preview"

                    with st.expander(f"📄 {m['name']} (Paper {m['paper_num']})"):
                        st.markdown(f"""
                            <div style="background-color:#0a205a; padding:10px; border-radius:8px">
                                <b>📚 Subject:</b> {m['subject']} <br>
                                <b>🎓 Course:</b> {m['course']} <br>
                                <b>📅 Semester:</b> {m.get('sem')} <br>
                                <b>📝 Paper number:</b> {m['paper_num']} <br>
                                <b>📅 Year:</b> {m['year']} <br><br>
                                <a href="{download_url}" target="_blank" style="font-weight:bold; color:#3366cc;">📥 Download PDF</a>
                            </div>
                        """, unsafe_allow_html=True)
                        st.markdown(
                            f'<iframe src="{preview_url}" width="700" height="500" style="border:1px solid #ccc; border-radius:8px;" allow="autoplay"></iframe>',
                            unsafe_allow_html=True
                        )

        except Exception as e:
            st.error(f"❌ Error loading Drive files: {e}")
            st.stop()

else:
    st.write("Alright, feel free to come back later when you're ready to search for PYQs.")

# 👣 Footer
st.markdown("""
<hr>
<p style='font-size:14px; color:#888888;'>Built with ❤️ using Streamlit · Powered by Google Drive · NLP search enabled</p>
""", unsafe_allow_html=True)
