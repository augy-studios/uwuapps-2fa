"""
Supabase client — used to look up uwu_users records.
We use the service role key so we can query by email or username
without needing the user to be authenticated on the Supabase side.
"""

import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logger = logging.getLogger(__name__)

_client: Client = None


def get_supabase() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _client


def find_uwu_user_by_identifier(identifier: str) -> dict | None:
    """
    Look up a uwu_users row by username or email.
    Returns the row as a dict, or None if not found.
    """
    sb = get_supabase()
    identifier = identifier.strip()

    # Try username first
    resp = (
        sb.table("uwu_users")
        .select("id, username, email, display_name, avatar_url")
        .eq("username", identifier)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]

    # Fall back to email
    resp = (
        sb.table("uwu_users")
        .select("id, username, email, display_name, avatar_url")
        .eq("email", identifier)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]

    return None


def find_uwu_user_by_id(user_id: str) -> dict | None:
    """
    Look up a uwu_users row by UUID.
    Returns the row as a dict, or None if not found.
    """
    sb = get_supabase()
    resp = (
        sb.table("uwu_users")
        .select("id, username, email, display_name, avatar_url")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if resp.data:
        return resp.data[0]
    return None