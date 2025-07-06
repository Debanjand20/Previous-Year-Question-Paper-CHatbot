import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        "service_account.json",  # Place this securely or use Streamlit secrets
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

    subjects = list_folders(root_folder_id)
    for subj in subjects:
        subj_name = subj["name"]
        subj_id = subj["id"]
        courses = list_folders(subj_id)
        for course in courses:
            course_name = course["name"]
            course_id = course["id"]
            sem_folders = list_folders(course_id)
            for sem in sem_folders:
                sem_name = sem["name"]
                sem_id = sem["id"]
                pdfs = list_pdfs(sem_id)
                for pdf in pdfs:
                    year_match = re.search(r'(\d{4})', pdf["name"])
                    year = int(year_match.group(1)) if year_match else None
                    if requested_year is None or (year == requested_year):
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
