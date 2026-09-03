from __future__ import annotations

import base64
import win32crypt


def protect_text(value: str) -> str:
    encrypted = win32crypt.CryptProtectData(value.encode("utf-8"), "AutoApply credential", None, None, None, 0)
    return base64.b64encode(encrypted).decode("ascii")


def unprotect_text(value: str) -> str:
    _, decrypted = win32crypt.CryptUnprotectData(base64.b64decode(value), None, None, None, 0)
    return decrypted.decode("utf-8")
