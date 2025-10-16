import os
import logging
import gc
import logging
from flask import (
    redirect,
    url_for, flash, session,
    Blueprint, render_template, jsonify
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


@main_bp.route('/upload_all_files', methods=['GET'])
def upload_all_files():
    folder_path = r"C:\Users\DannyLiang-Geosource\Downloads\rig_test_folder"
    folder = Path(folder_path).expanduser().resolve()
    if not folder.exists():
        raise FileNotFoundError(f"Folder {folder} does not exist")
    if not folder.is_dir():
        raise NotADirectoryError(f"Folder {folder} is not a directory")
    allowed_ext = {".csv", ".xlsx", ".xls", ".pdf"}
    uploaded = []

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in allowed_ext:
            uploaded.append(file)
    print(uploaded)  # for debugging in console
    # return jsonify([str(f) for f in uploaded])
    return uploaded


def save_to_sred(files):
    """
    Upload exactly the file the user uploaded to SharePoint.
    - CSV -> Data/{rig}/
    - Others -> Reports/{rig}/
    """
    rig = "360"  # figure out a way to get rig number from session, wait to get file name first
    date = "10_15_2028"
    ctx = ClientContext(SP_SITE_URL).with_credentials(
        ClientCredential(SP_CLIENT_ID, SP_CLIENT_SECRET)
    )
    folder = ctx.web.get_folder_by_server_relative_url(
        f"{SP_DOC_LIBRARY}/Reports/{rig}"
    )
    ctx.load(folder, ["Files"]).execute_query()
    existing = [f.properties["Name"] for f in folder.files]

    for file in files:
        try:
            p = file if isinstance(file, Path) else Path(file)
            filename = p.name
            ext = p.suffix.lower()

            new_name = filename
            if file.name in existing:
                base, e = os.path.splitext(filename)
                i = 1
                while filename in existing:
                    new_name = f"{base} ({i}){e}"
                    i += 1

            # Read file bytes and upload
            data = file.read_bytes()  # bytes
            folder.upload_file(new_name, data).execute_query()
            del data
            flash("Report saved to SR&ED successfully.", "success")
            gc.collect()

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
