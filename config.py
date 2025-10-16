import os
import getpass
import secrets

if os.environ.get("FLASK_ENV") != "production":
    from dotenv import load_dotenv
    load_dotenv()

APP_PASSWORD = os.environ.get("GEOMETRICS_PASSWORD")

SECRET_KEY = secrets.token_hex(16)
USERNAME   = getpass.getuser()

BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_FILE_PATH = os.path.join(
    BASE_DIR,
    'REPORT_TEMPLATE.xlsx'
)

ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

SP_SITE_URL      = os.getenv("SP_SITE_URL", "")
SP_DOC_LIBRARY   = os.getenv("SP_DOC_LIBRARY", "")
SP_CLIENT_ID     = os.getenv("SP_CLIENT_ID", "")
SP_CLIENT_SECRET = os.getenv("SP_CLIENT_SECRET", "")
SP_TENANT_ID     = os.getenv("SP_TENANT_ID", "")
