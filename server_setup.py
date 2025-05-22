# server_setup.py
import os
import writer.serve
import writer.auth
from fastapi import Request, Response
from urllib.parse import urlparse
import json # Import json for pretty printing

# --- (Keep your Configuration and OIDC Endpoints sections as they are) ---
# --- Configuration ---
CLIENT_ID = os.getenv("MS_CLIENT_ID")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
TENANT_ID = os.getenv("MS_TENANT_ID") # Your Azure AD Tenant ID
HOST_URL = os.getenv("HOST_URL", "http://localhost:3005") # Your app's base URL
ALLOWED_TENANT_ID = os.getenv("ALLOWED_TENANT_ID", TENANT_ID)
# ---------------------

# --- Microsoft OIDC Endpoints ---
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
AUTHORIZE_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"
USERINFO_ENDPOINT = "https://graph.microsoft.com/oidc/userinfo"
# --------------------------------

# --- Input Validation ---
if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, ALLOWED_TENANT_ID]):
    print("ERROR: Missing required environment variables...")
# ------------------------

# --- OIDC Configuration ---
oidc_config = writer.auth.Oidc(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    host_url=HOST_URL,
    url_authorize=AUTHORIZE_ENDPOINT,
    url_oauthtoken=TOKEN_ENDPOINT,
    url_userinfo=USERINFO_ENDPOINT,
    scope="openid profile email User.Read offline_access", # Keep User.Read for now
)
# --------------------------


# --- TEMPORARY DEBUGGING Authorization Callback ---
def check_enterprise_user(request: Request, session_id: str, userinfo: dict):
    """
    TEMPORARY DEBUGGING VERSION: Prints the full userinfo and allows access.
    """
    print("-" * 20)
    print("DEBUG: Received userinfo:")
    # Pretty print the dictionary for easier reading
    print(json.dumps(userinfo, indent=2))
    print("-" * 20)

    # Temporarily allow access to see the claims
    print(f"DEBUG: Temporarily allowing access for user {userinfo.get('email')}")
    return # Allow access for debugging purposes
# -------------------------------------------------

# --- Register Authentication ---
if all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, ALLOWED_TENANT_ID]):
    print(f"Registering Microsoft Entra ID OIDC authentication for tenant {ALLOWED_TENANT_ID} (DEBUG MODE - ALL USERS ALLOWED)")
    writer.serve.register_auth(oidc_config, callback=check_enterprise_user)
else:
    print("Skipping authentication registration due to missing environment variables.")
# -----------------------------