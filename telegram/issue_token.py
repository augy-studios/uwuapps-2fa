"""
issue_token.py — CLI utility to insert a deep-link login token into Supabase.
Used for testing or as a reference for web app backend integration.

Usage:
    python issue_token.py <uwu_user_id> [app_id] [app_label]

Example:
    python issue_token.py "uuid-here" "mrt-app" "UwU MRT Info"

The token is then embedded in the Telegram deep link:
    https://t.me/uwuapps_2fa_bot?start=<token>
"""

import sys
import secrets
from supabase_db import insert_token
from config import TOKEN_EXPIRY_SECONDS


def main():
    if len(sys.argv) < 2:
        print("Usage: python issue_token.py <uwu_user_id> [app_id] [app_label]")
        sys.exit(1)

    uwu_user_id = sys.argv[1]
    app_id      = sys.argv[2] if len(sys.argv) > 2 else "uwuapps"
    app_label   = sys.argv[3] if len(sys.argv) > 3 else "UwU Apps"

    token = secrets.token_urlsafe(32)
    insert_token(token, uwu_user_id, app_id, app_label, TOKEN_EXPIRY_SECONDS)

    deep_link = f"https://t.me/uwuapps_2fa_bot?start={token}"
    print(f"Token : {token}")
    print(f"Link  : {deep_link}")
    print(f"Expiry: {TOKEN_EXPIRY_SECONDS}s")


if __name__ == "__main__":
    main()