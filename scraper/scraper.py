import os
import io
import pickle
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def authenticate_google_drive():
    """Authenticate using OAuth 2.0 credentials from environment variables."""
    creds = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = Credentials(
                token=None,
                refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
                client_id=os.getenv("GOOGLE_CLIENT_ID"),
                client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
                token_uri="https://oauth2.googleapis.com/token",
            )

    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def download_google_sheets_as_csv(service, folder_id, output_dir="rosters"):
    """Download Google Sheets files as CSV from a Google Drive folder."""
    try:
        # Query to find Google Sheets files in the folder
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        if not files:
            print("No Google Sheets files found.")
            return

        os.makedirs(output_dir, exist_ok=True)

        # Download each Google Sheets file as CSV
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            file_path = os.path.join(output_dir, f"{file_name}.csv")

            # Export Google Sheets file as CSV
            request = service.files().export_media(
                fileId=file_id,
                mimeType="text/csv"
            )

            with io.FileIO(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"Downloaded {file_name}.csv: {int(status.progress() * 100)}%")

            print(f"Saved to {file_path}")

    except HttpError as error:
        print(f"Error: {error}")

if __name__ == "__main__":
    service = authenticate_google_drive()
    folder_id = "1SCJY626xXyZDaB9qdbSpcxeaYWwD8fYL"  # Replace with your folder ID
    download_google_sheets_as_csv(service, folder_id)