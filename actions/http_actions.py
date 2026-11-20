# actions/http_actions.py
"""
HTTP request action using only the standard library (no new dependencies).

Responses are stored in the shared variable context so later blocks can
use them (Condition checks, {{var}} interpolation, notifications...).
"""

import urllib.error
import urllib.request

from .base_action import BaseAction, ActionResult

DEFAULT_USER_AGENT = "FlowMatic/1.0"


class HttpRequestAction(BaseAction):
    """Performs an HTTP request and stores the response in a variable."""

    ACTION_TYPE = "http_request"
    ACTION_LABEL = "HTTP Request"
    ACTION_ICON_KEY = "globe"
    ACTION_COLOR = "#2980B9"
    ACTION_DESCRIPTION = "Call a REST API and save the response into a variable."

    METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]

    def _init_params(self):
        self._params = {
            "method": "GET",
            "url": "",
            "headers": "",             # one per line: "Key: Value"
            "body": "",                # request body (POST/PUT/PATCH)
            "timeout": 10.0,           # seconds
            "save_to_var": "http_response",
        }

    def _parse_headers(self, raw: str) -> dict:
        headers = {}
        for line in (raw or "").splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            headers[key.strip()] = value.strip()
        return headers

    def _save_response(self, status: int, body: str):
        name = str(self.get_param("save_to_var", "")).strip()
        if not name:
            return
        self.set_var(name, body)
        self.set_var(f"{name}_status", status)

    def execute(self) -> ActionResult:
        url = self.interpolate(self.get_param("url", "")).strip()
        if not url:
            return ActionResult(False, "No URL specified.")
        if not url.lower().startswith(("http://", "https://")):
            return ActionResult(False, f"URL must start with http:// or https://: {url}")

        method = str(self.get_param("method", "GET")).upper()
        if method not in self.METHODS:
            return ActionResult(False, f"Unsupported method: {method}")

        try:
            timeout = float(self.get_param("timeout", 10.0))
        except (TypeError, ValueError):
            timeout = 10.0
        timeout = max(1.0, min(timeout, 300.0))

        headers = {
            self.interpolate(k): self.interpolate(v)
            for k, v in self._parse_headers(self.get_param("headers", "")).items()
        }
        headers.setdefault("User-Agent", DEFAULT_USER_AGENT)

        body = self.interpolate(self.get_param("body", ""))
        data = body.encode("utf-8") if body and method not in ("GET", "HEAD") else None
        if data is not None and "content-type" not in {k.lower() for k in headers}:
            headers["Content-Type"] = "text/plain"

        req = urllib.request.Request(url, data=data, method=method, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", None) or resp.getcode()
                text = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            try:
                text = e.read().decode("utf-8", errors="replace")
            except Exception:
                text = ""
            self._save_response(status=e.code, body=text)
            return ActionResult(False, f"HTTP {e.code} {e.reason} — {url}", {"status": e.code})
        except urllib.error.URLError as e:
            return ActionResult(False, f"Request failed: {e.reason} — {url}")
        except Exception as e:
            return ActionResult(False, f"Request failed: {e}")

        self._save_response(status=status, body=text)
        preview = text[:80] + ("…" if len(text) > 80 else "")
        return ActionResult(True, f"HTTP {status} — {preview}", {"status": status})

    def get_summary(self) -> str:
        method = str(self.get_param("method", "GET")).upper()
        url = self.get_param("url", "")
        if url:
            return f"{method}: {url[:40]}" + ("…" if len(url) > 40 else "")
        return "HTTP Request (not configured)"
