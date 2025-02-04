import os
import io
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

def authenticate_google_drive():
    """Authenticate and return the Google Drive API service."""
    creds, _ = google.auth.default()
    service = build("drive", "v3", credentials=creds)
    return service


def download_csv_files(service, folder_id, output_dir):
    """
    Download all CSV files from a Google Drive folder.

    Args:
        service: Google Drive API service object.
        folder_id: ID of the Google Drive folder containing the CSV files.
        output_dir: Local directory to save the downloaded files.
    """
    try:
        # Query to find CSV files in the folder
        query = f"'{folder_id}' in parents and mimeType='text/csv'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get("files", [])

        if not files:
            print("No CSV files found in the folder.")
            return

        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Download each CSV file
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            request = service.files().get_media(fileId=file_id)
            file_path = os.path.join(output_dir, file_name)

            with io.FileIO(file_path, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    print(f"Downloaded {file_name}: {int(status.progress() * 100)}%")

            print(f"Saved {file_name} to {file_path}")

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    # Authenticate and get the Google Drive service
    service = authenticate_google_drive()

    # Specify the Google Drive folder ID and output directory
    folder_id = "1SCJY626xXyZDaB9qdbSpcxeaYWwD8fYL"  # Replace with your folder ID
    output_dir = "rosters"  # Directory to save downloaded CSVs

    # Download CSV files
    download_csv_files(service, folder_id, output_dir)