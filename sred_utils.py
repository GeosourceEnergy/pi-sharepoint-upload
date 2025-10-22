import os
import gc
import time
import subprocess

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import (
    SP_SITE_URL, SP_DOC_LIBRARY,
    SP_CLIENT_ID, SP_CLIENT_SECRET
)

from pathlib import Path


def get_files_from_folder():
    folder_path = r"C:\Users\DannyLiang-Geosource\Downloads\rig_test_folder"
    # folder_path = r"/home/admin/Downloads/rig_test_folder"
    # folder_path = "/media/username/BEA6-BBCE1/usb_share"
    mount_path = r"/home/username/Desktop/mountdrive.sh"
    mount_execute = subprocess.run(["bash", mount_path], capture_output=True, text=True)
    if mount_execute.returncode != 0:
        raise Exception(f"Failed to mount drive: {mount_execute.stderr}")
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder} does not exist")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder {folder} is not a directory")
    # Update to files that are being uploaded, this should be all based on Amanda's messages
    allowed_ext = {".csv", ".xlsx", ".xls"}
    uploaded = []

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in allowed_ext:
            uploaded.append(file)
    print(uploaded)  # for debugging in console
    # return jsonify([str(f) for f in uploaded])
    return uploaded

# Function to save files to SharePoint, not automated for 7pm yet


def save_to_sred(files):
    """
    Upload exactly the file the user uploaded to SharePoint.
    - CSV -> Data/{rig}/
    - Others -> Reports/{rig}/
    """

    rig = "360"  # figure out a way to get rig number from session, wait to get file name first
    # figure out a way to get date from session, wait to get file name first
    date = "10_15_2028"
    # Authenticating with Sharepoint site using app credentials
    ctx = ClientContext(SP_SITE_URL).with_credentials(
        ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
    )

    # Update folder and path in .env file after final file names are created
    folder = ctx.web.get_folder_by_server_relative_url(
        f"{SP_DOC_LIBRARY}/Reports/{rig}"
    )

    unmount_path = r"/home/username/Desktop/unmountdrive.sh"

    # Load existing files in the folder
    ctx.load(folder, ["Files"]).execute_query()

    # Stores existing filenames
    existing = {f.properties["Name"] for f in folder.files}

    # Iterate through files and upload to SharePoint
    for file in files:
        try:
            t_file = time.perf_counter()  # Start timing for file processing
            # Convert file to Path object if it's not already
            p = file if isinstance(file, Path) else Path(file)
            filename = p.name
            ext = p.suffix.lower()  # file type

            # Preparing new file name, if file already exists, add a number to the end
            new_name = filename
            base, e = os.path.splitext(filename)
            i = 1
            # Loop until name is unique in SharePoint folder
            while new_name in existing:
                new_name = f"{base} ({i}){e}"
                i += 1

            # Read file bytes and upload
            t_read = time.perf_counter()
            data = file.read_bytes()  # bytes
            # Log size instead of raw bytes to prevent console overload

            # Upload file to SharePoint
            folder.upload_file(new_name, data).execute_query()
            del data
            gc.collect()  # Force garbage collection after large file uploads (optional safeguard)

        except Exception as e:
            print(f"Error saving to SR&ED: {e}")
    unmount_execute = subprocess.run(["bash", unmount_path], capture_output=True, text=True)
    if unmount_execute.returncode != 0:
        raise Exception(f"Failed to unmount drive: {unmount_execute.stderr}")


def run_auto_save_sred():
    files = get_files_from_folder()
    save_to_sred(files)
    return
