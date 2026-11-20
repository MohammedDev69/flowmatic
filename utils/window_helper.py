# utils/window_helper.py
"""
Cross-platform helpers for finding and controlling application windows.
On Windows uses Win32 APIs for reliable minimize/restore/focus from background threads.
"""

from __future__ import annotations

import sys
from typing import List, Tuple


def list_open_window_titles() -> List[str]:
    """Return sorted unique titles of visible windows with non-empty titles."""
    try:
        import pygetwindow as gw
    except Exception:
        return []

    titles: List[str] = []
    seen: set[str] = set()
    for win in gw.getAllWindows():
        title = (win.title or "").strip()
        if not title or title in seen:
            continue
        width = getattr(win, "width", 0) or 0
        height = getattr(win, "height", 0) or 0
        if width <= 0 and height <= 0:
            continue
        seen.add(title)
        titles.append(title)
    return sorted(titles, key=str.lower)


def find_windows_by_title(partial: str) -> list:
    """Return pygetwindow windows whose title contains partial (case-insensitive)."""
    needle = (partial or "").strip().lower()
    if not needle:
        return []
    try:
        import pygetwindow as gw
    except Exception:
        return []

    matches = []
    for win in gw.getAllWindows():
        title = (win.title or "").strip()
        if not title:
            continue
        if needle in title.lower():
            matches.append(win)
    return matches


def _win32_show(hwnd: int, maximize: bool = False) -> bool:
    import ctypes

    user32 = ctypes.windll.user32
    SW_RESTORE = 9
    SW_SHOW = 5
    SW_MAXIMIZE = 3
    VK_MENU = 0x12
    KEYEVENTF_KEYUP = 0x0002

    if not hwnd or not user32.IsWindow(hwnd):
        return False

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    else:
        user32.ShowWindow(hwnd, SW_SHOW)

    if maximize:
        user32.ShowWindow(hwnd, SW_MAXIMIZE)

    # Windows blocks background focus changes unless input is "allowed".
    user32.keybd_event(VK_MENU, 0, 0, 0)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)

    foreground = user32.GetForegroundWindow()
    if foreground != hwnd:
        fg_thread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
        target_thread = user32.GetWindowThreadProcessId(hwnd, None)
        if fg_thread and target_thread and fg_thread != target_thread:
            user32.AttachThreadInput(fg_thread, target_thread, True)
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)
        if fg_thread and target_thread and fg_thread != target_thread:
            user32.AttachThreadInput(fg_thread, target_thread, False)

    return True


def _win32_hide(hwnd: int) -> bool:
    import ctypes

    user32 = ctypes.windll.user32
    SW_MINIMIZE = 6
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    return bool(user32.ShowWindow(hwnd, SW_MINIMIZE))


def _pygetwindow_show(win, maximize: bool = False) -> bool:
    if getattr(win, "isMinimized", False):
        win.restore()
    if maximize:
        win.maximize()
    else:
        try:
            win.show()
        except Exception:
            pass
    win.activate()
    return True


def show_windows_by_title(title: str, maximize: bool = False) -> Tuple[bool, str, list]:
    windows = find_windows_by_title(title)
    if not windows:
        return False, f"No window found with title containing: '{title}'", []

    shown = []
    last_error = ""
    for win in windows:
        try:
            if sys.platform == "win32":
                hwnd = getattr(win, "_hWnd", 0)
                if hwnd and _win32_show(hwnd, maximize):
                    shown.append(win.title)
                    continue
            _pygetwindow_show(win, maximize)
            shown.append(win.title)
        except Exception as exc:
            last_error = str(exc)

    if shown:
        return True, f"Showed {len(shown)} window(s): {shown[0][:40]}", shown
    msg = f"Failed to show window: {title}"
    if last_error:
        msg += f" ({last_error})"
    return False, msg, []


def hide_windows_by_title(title: str) -> Tuple[bool, str, list]:
    windows = find_windows_by_title(title)
    if not windows:
        return False, f"No window found with title containing: '{title}'", []

    hidden = []
    last_error = ""
    for win in windows:
        try:
            ok = False
            if sys.platform == "win32":
                hwnd = getattr(win, "_hWnd", 0)
                if hwnd:
                    ok = _win32_hide(hwnd)
            if not ok:
                win.minimize()
            hidden.append(win.title)
        except Exception as exc:
            last_error = str(exc)

    if hidden:
        return True, f"Minimized {len(hidden)} window(s): {hidden[0][:40]}", hidden
    msg = f"Failed to hide window: {title}"
    if last_error:
        msg += f" ({last_error})"
    return False, msg, []
