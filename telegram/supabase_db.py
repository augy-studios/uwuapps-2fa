"""
supabase_db.py — All bot data stored in Supabase.

Tables (create via migration.sql):
  uwutele_links       — Telegram <-> UwU Apps account linkages
  uwutele_tokens      — Pending deep-link login tokens (Flow A)
  uwutele_otps        — Bot-generated OTP codes (Flow B)
  uwutele_sessions    — Completed login sessions (audit trail)
  uwutele_link_state  — In-progress /link conversation state
  uwutele_buttons     — Persisted inline keyboard button states
"""

import logging
from datetime import datetime, timezone, timedelta
from supabase import Client
from supabase_client import get_supabase
from config import TOKEN_EXPIRY_SECONDS

logger = logging.getLogger(__name__)


def _sb() -> Client:
    return get_supabase()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _expiry_iso(seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


# ── Link helpers ───────────────────────────────────────────────────────────────

def get_link_by_telegram(telegram_id: int) -> dict | None:
    resp = (
        _sb().table("uwutele_links")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def get_link_by_uwu_user(uwu_user_id: str) -> dict | None:
    resp = (
        _sb().table("uwutele_links")
        .select("*")
        .eq("uwu_user_id", uwu_user_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def upsert_link(telegram_id: int, telegram_username: str,
                uwu_user_id: str, uwu_username: str,
                uwu_email: str, uwu_display_name: str):
    _sb().table("uwutele_links").upsert(
        {
            "telegram_id":       telegram_id,
            "telegram_username": telegram_username,
            "uwu_user_id":       uwu_user_id,
            "uwu_username":      uwu_username,
            "uwu_email":         uwu_email,
            "uwu_display_name":  uwu_display_name,
            "linked_at":         _now_iso(),
        },
        on_conflict="telegram_id",
    ).execute()


def delete_link(telegram_id: int):
    _sb().table("uwutele_links").delete().eq("telegram_id", telegram_id).execute()


# ── Token helpers (Flow A — web-app-initiated deep link) ──────────────────────

def insert_token(token: str, uwu_user_id: str, app_id: str,
                 app_label: str, expiry_seconds: int):
    _sb().table("uwutele_tokens").insert({
        "token":       token,
        "uwu_user_id": uwu_user_id,
        "app_id":      app_id,
        "app_label":   app_label,
        "expires_at":  _expiry_iso(expiry_seconds),
    }).execute()


def get_valid_token(token: str) -> dict | None:
    now = _now_iso()
    resp = (
        _sb().table("uwutele_tokens")
        .select("*")
        .eq("token", token)
        .eq("used", False)
        .gt("expires_at", now)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def mark_token_used(token: str):
    _sb().table("uwutele_tokens").update({
        "used":    True,
        "used_at": _now_iso(),
    }).eq("token", token).execute()


def purge_expired_tokens():
    now = _now_iso()
    _sb().table("uwutele_tokens").delete().eq("used", False).lt("expires_at", now).execute()


# ── OTP helpers (Flow B — bot-initiated) ──────────────────────────────────────

def insert_otp(otp: str, telegram_id: int, uwu_user_id: str,
               app_id: str, expiry_seconds: int):
    _sb().table("uwutele_otps").insert({
        "otp":         otp,
        "telegram_id": telegram_id,
        "uwu_user_id": uwu_user_id,
        "app_id":      app_id,
        "expires_at":  _expiry_iso(expiry_seconds),
    }).execute()


def get_valid_otp(otp: str) -> dict | None:
    now = _now_iso()
    resp = (
        _sb().table("uwutele_otps")
        .select("*")
        .eq("otp", otp)
        .eq("used", False)
        .gt("expires_at", now)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def get_active_otp_for_user(telegram_id: int) -> dict | None:
    now = _now_iso()
    resp = (
        _sb().table("uwutele_otps")
        .select("*")
        .eq("telegram_id", telegram_id)
        .eq("used", False)
        .gt("expires_at", now)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def mark_otp_used(otp: str):
    _sb().table("uwutele_otps").update({
        "used":    True,
        "used_at": _now_iso(),
    }).eq("otp", otp).execute()


def purge_expired_otps():
    now = _now_iso()
    _sb().table("uwutele_otps").delete().eq("used", False).lt("expires_at", now).execute()


# ── Session helpers ────────────────────────────────────────────────────────────

def record_session(token: str, telegram_id: int, uwu_user_id: str, app_id: str):
    _sb().table("uwutele_sessions").insert({
        "token":       token,
        "telegram_id": telegram_id,
        "uwu_user_id": uwu_user_id,
        "app_id":      app_id,
    }).execute()


# ── Link state helpers (conversation tracking) ─────────────────────────────────

def set_link_state(telegram_id: int, step: str, identifier: str = None):
    _sb().table("uwutele_link_state").upsert(
        {
            "telegram_id": telegram_id,
            "step":        step,
            "identifier":  identifier,
            "updated_at":  _now_iso(),
        },
        on_conflict="telegram_id",
    ).execute()


def get_link_state(telegram_id: int) -> dict | None:
    resp = (
        _sb().table("uwutele_link_state")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def clear_link_state(telegram_id: int):
    _sb().table("uwutele_link_state").delete().eq("telegram_id", telegram_id).execute()


# ── Button persistence helpers ─────────────────────────────────────────────────

def persist_button(message_id: str, chat_id: int, button_data: str, handler: str):
    _sb().table("uwutele_buttons").upsert(
        {
            "message_id":  str(message_id),
            "chat_id":     chat_id,
            "button_data": button_data,
            "handler":     handler,
        },
        on_conflict="message_id,chat_id,button_data",
    ).execute()


def get_button_handler(message_id: str, chat_id: int, button_data: str) -> str | None:
    resp = (
        _sb().table("uwutele_buttons")
        .select("handler")
        .eq("message_id", str(message_id))
        .eq("chat_id", chat_id)
        .eq("button_data", button_data)
        .limit(1)
        .execute()
    )
    return resp.data[0]["handler"] if resp.data else None