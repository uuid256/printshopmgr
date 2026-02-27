"""
Accounts views — login/logout handled by Django built-ins in urls.py.

LINE Login OAuth views allow staff to connect their personal LINE account
so they receive owner/staff notifications via LINE.
"""

import uuid

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


def _line_login_callback_url(request):
    """Build the absolute callback URL for LINE OAuth redirect_uri."""
    return request.build_absolute_uri("/accounts/line-callback/")


@login_required
def line_login_redirect(request):
    """
    Build the LINE Login OAuth authorisation URL and redirect the user to it.

    Stores a random state token in the session to guard against CSRF.
    """
    channel_id = getattr(settings, "LINE_LOGIN_CHANNEL_ID", "")
    if not channel_id:
        messages.error(request, "LINE Login ยังไม่ได้ตั้งค่า (LINE_LOGIN_CHANNEL_ID missing)")
        return redirect("notifications:settings")

    state = str(uuid.uuid4())
    request.session["line_oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": channel_id,
        "redirect_uri": _line_login_callback_url(request),
        "state": state,
        "scope": "profile",
    }
    from urllib.parse import urlencode

    auth_url = "https://access.line.me/oauth2/v2.1/authorize?" + urlencode(params)
    return redirect(auth_url)


@login_required
def line_login_callback(request):
    """
    Handle the LINE Login OAuth callback.

    Exchanges the authorisation code for an access token, fetches the user
    profile, and stores line_user_id + line_display_name on the Django user.
    """
    error = request.GET.get("error")
    if error:
        messages.error(request, f"LINE Login ล้มเหลว: {request.GET.get('error_description', error)}")
        return redirect("notifications:settings")

    state = request.GET.get("state")
    expected_state = request.session.pop("line_oauth_state", None)
    if not state or state != expected_state:
        messages.error(request, "LINE Login: state ไม่ตรงกัน (อาจมีการโจมตี CSRF)")
        return redirect("notifications:settings")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "LINE Login: ไม่ได้รับ authorisation code")
        return redirect("notifications:settings")

    channel_id = getattr(settings, "LINE_LOGIN_CHANNEL_ID", "")
    channel_secret = getattr(settings, "LINE_LOGIN_CHANNEL_SECRET", "")

    # Exchange code for access token
    try:
        token_resp = requests.post(
            "https://api.line.me/oauth2/v2.1/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _line_login_callback_url(request),
                "client_id": channel_id,
                "client_secret": channel_secret,
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]
    except Exception as exc:
        messages.error(request, f"LINE Login: token exchange ล้มเหลว ({exc})")
        return redirect("notifications:settings")

    # Fetch profile
    try:
        profile_resp = requests.get(
            "https://api.line.me/v2/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()
        line_user_id = profile["userId"]
        line_display_name = profile.get("displayName", "")
    except Exception as exc:
        messages.error(request, f"LINE Login: ดึงข้อมูลโปรไฟล์ล้มเหลว ({exc})")
        return redirect("notifications:settings")

    request.user.line_user_id = line_user_id
    request.user.line_display_name = line_display_name
    request.user.save(update_fields=["line_user_id", "line_display_name"])

    messages.success(request, f"เชื่อมต่อ LINE สำเร็จ: {line_display_name}")
    return redirect("notifications:settings")


@login_required
@require_POST
def line_disconnect(request):
    """Clear the user's LINE account connection."""
    request.user.line_user_id = ""
    request.user.line_display_name = ""
    request.user.save(update_fields=["line_user_id", "line_display_name"])
    messages.success(request, "ยกเลิกการเชื่อมต่อ LINE แล้ว")
    return redirect("notifications:settings")
