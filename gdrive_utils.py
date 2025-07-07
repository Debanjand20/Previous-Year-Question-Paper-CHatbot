import re
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    # Load credentials from Streamlit secrets
    service_account_info = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

def list_pdf_metadata(service, root_folder_id, requested_year):
    metadata = []

    def list_folders(parent_id):
        folders = []
        page_token = None
        while True:
            response = service.files().list(
                q=f"'{parent_id}' in parents and mimeType='application/vnd.google-apps.folder'",
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=page_token
            ).execute()
            folders.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return folders

    def list_pdfs(folder_id):
        pdfs = []
        page_token = None
        while True:
            response = service.files().list(
                q=f"'{folder_id}' in parents and mimeType='application/pdf'",
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=page_token
            ).execute()
            pdfs.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return pdfs

    # Step 1: Year folders (e.g., "2020", "2021", etc.)
    year_folders = list_folders(root_folder_id)

    for year_folder in year_folders:
        year_name = year_folder["name"]
        year_id = year_folder["id"]

        # Extract year from folder name using regex
        year_match = re.search(r'\d{4}', year_name)
        year = int(year_match.group(0)) if year_match else None

        # Skip if year is provided and does not match
        if requested_year is not None and year != requested_year:
            continue

        # Step 2: Subject folders under each year
        subjects = list_folders(year_id)

        for subj in subjects:
            subj_name = subj["name"]
            subj_id = subj["id"]

            # Step 3: Gen / Hons under each subject
            courses = list_folders(subj_id)

            for course in courses:
                course_name = course["name"]
                course_id = course["id"]

                # Step 4: Semester folders under Gen/Hons
                sem_folders = list_folders(course_id)

                for sem in sem_folders:
                    sem_name = sem["name"]
                    sem_id = sem["id"]

                    # Step 5: PDF files in sem folder
                    pdfs = list_pdfs(sem_id)

                    for pdf in pdfs:
                        metadata.append({
                            "id": pdf["id"],
                            "name": pdf["name"],
                            "subject": subj_name,
                            "course": course_name,
                            "semester_folder": sem_name,
                            "year": year
                        })

    return metadata

def file_link(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"
