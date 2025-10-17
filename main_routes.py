import os
import logging
import gc
import time
from flask import (
    redirect,
    url_for, flash,
    Blueprint, render_template, jsonify, current_app
)

from office365.runtime.auth.client_credential import ClientCredential
from office365.sharepoint.client_context import ClientContext

from config import (
    SP_SITE_URL, SP_DOC_LIBRARY,
    SP_CLIENT_ID, SP_CLIENT_SECRET
)

from pathlib import Path

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


# Temporary funciton that  gets files from my local folder
# Should be replaced with a path to the raspberry pi folder
@main_bp.route('/upload_all_files', methods=['GET'])
def upload_all_files():
    folder_path = r"C:\Users\DannyLiang-Geosource\Downloads\rig_test_folder"
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
    # tries to get curret_app.logger attribute, creates standard python logger after the current module __name__
    logger = getattr(current_app, 'logger', logging.getLogger(__name__))

    # Helper function to log to console and file
    def log(msg):
        if logger:
            logger.info(msg)
        print(msg, flush=True)

    rig = "360"  # figure out a way to get rig number from session, wait to get file name first
    date = "10_15_2028" # figure out a way to get date from session, wait to get file name first
    log("Save to sred called") 
    # Authenticating with Sharepoint site using app credentials
    ctx = ClientContext(SP_SITE_URL).with_credentials(
        ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
    )
    log(f"Client context created/authentication: {ctx}")

    # Access target folder on sharepoint (/Documents/reports/rig_number)
    # Update folder and path in .env file after final file names are created
    folder = ctx.web.get_folder_by_server_relative_url(
        f"{SP_DOC_LIBRARY}/Reports/{rig}"
    )
    log(f"Folder created: {folder}")

    # Load existing files in the folder
    ctx.load(folder, ["Files"]).execute_query()
    log(f"Folder loaded: {folder}")

    # Stores existing filenames
    existing = {f.properties["Name"] for f in folder.files}
    log(f"Existing files: {existing}")
    log(f"SharePoint: loaded {len(existing)} names")

    # Iterate through files and upload to SharePoint
    log(f"Starting file upload for files: {files}")
    for file in files:
        try:
            t_file = time.perf_counter() # Start timing for file processing
            p = file if isinstance(file, Path) else Path(file) # Convert file to Path object if it's not already
            filename = p.name
            ext = p.suffix.lower() # file type
            log(f"File: {filename} (ext: {ext}) (elapsed {time.perf_counter() - t_file:.3f}s)")

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
            log(f"Read {len(data)} bytes "
                f"(elapsed {time.perf_counter() - t_read:.3f}s)")

            # Upload file to SharePoint
            folder.upload_file(new_name, data).execute_query()
            del data
            log(f"Uploaded file: {new_name}")
            flash("Report saved to SR&ED successfully.", "success")
            gc.collect()  # Force garbage collection after large file uploads (optional safeguard)

        except Exception as e:
            logging.error("Error saving to SR&ED", exc_info=True)
            flash(f"Error saving to SR&ED: {e}", "error")
    return redirect(url_for('main.index'))


@main_bp.route('/save_report_sred', methods=['POST'])
def run_folder_batch():
    try:
        # 1) get everything in the folder
        files = upload_all_files()
        uploaded = save_to_sred(files)  # 2) iterate & upload

        msg = [f"Uploaded {uploaded}"]
        flash(" | ".join(msg), "success")
    except Exception as e:
        logging.exception("Batch upload failed")
        flash(f"Batch upload failed: {e}", "error")
    return redirect(url_for('main.index'))
