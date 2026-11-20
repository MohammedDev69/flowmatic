# ⬡ FlowMatic — Visual Automation Tool

A professional desktop automation application built with Python + PySide6.
Create visual workflows by stacking action blocks, assign keyboard shortcuts,
and trigger complex automations with a single keystroke.

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install PySide6 psutil pygetwindow keyboard
```

> **Linux note:** The `keyboard` library requires root access for global hotkeys.
> Run with `sudo python main.py` or use `sudo pip install keyboard` to enable hotkeys.
> On Windows/macOS no elevated privileges are needed.

### 2. Run the application

```bash
cd flowmatic
python main.py
```

---

## 📁 Project Structure

```
flowmatic/
│
├── main.py                     # Entry point — run this
├── requirements.txt
│
├── actions/                    # Action block definitions
│   ├── __init__.py
│   ├── base_action.py          # Abstract BaseAction class + ActionResult
│   ├── program_actions.py      # OpenProgram, CloseProgram
│   ├── window_actions.py       # ShowWindow, HideWindow
│   ├── control_actions.py      # Wait, Condition, Loop
│   ├── keyboard_actions.py     # SendKeys (type text / hotkey combos)
│   ├── http_actions.py         # HTTP Request (stdlib urllib)
│   └── notify_actions.py       # Notify (desktop notification)
│
├── core/                       # Business logic
│   ├── __init__.py
│   ├── workflow.py             # Workflow data model
│   ├── engine.py               # Sequential execution engine (threaded)
│   └── registry.py             # Action type registry for serialization
│
├── ui/                         # All GUI components
│   ├── __init__.py
│   ├── main_window.py          # Root window — wires everything together
│   ├── theme.py                # Dark theme constants + QSS stylesheet
│   ├── icons.py                # Painted vector icons (no image assets)
│   ├── toolbar.py              # Top bar: Run / Stop / Save / Load / Settings
│   ├── palette_panel.py        # Left: draggable action type tiles
│   ├── workflow_canvas.py      # Center: drag-and-drop workflow builder
│   ├── block_widget.py         # Individual block card widget
│   ├── properties_panel.py     # Right: dynamic properties editor
│   ├── log_panel.py            # Bottom: real-time execution log
│   ├── workflow_list.py        # Workflow tabs (above palette)
│   ├── hotkey_dialog.py        # Keyboard shortcut recorder
│   └── settings_dialog.py      # App preferences (tray, notifications)
│
└── utils/                      # Utilities
    ├── __init__.py
    ├── file_manager.py         # JSON save/load
    ├── app_settings.py         # Persistent app settings (%APPDATA%/FlowMatic)
    ├── hotkey_manager.py       # Global hotkey registration
    ├── hotkey_format.py        # Hotkey string normalization
    ├── win_hotkey.py           # Windows RegisterHotKey backend
    └── window_helper.py        # Win32 window show/hide helpers
```

---

## 🎯 Features

### Block System
| Block | Description |
|-------|-------------|
| ▶ Open Program | Launch any .exe / script with optional arguments |
| ✕ Close Program | Terminate a process by name (graceful or force-kill) |
| ⌨ Send Keys | Type text or press a hotkey combo into the focused window |
| 🌐 HTTP Request | Call a REST API (GET/POST/PUT/PATCH/DELETE) and save the response |
| ⏱ Wait | Pause execution for N seconds |
| 👁 Show Window | Restore/focus a window by partial title |
| — Hide Window | Minimize a window to taskbar |
| 🔁 Loop | Repeat the next N blocks M times |
| ◇ Condition | If-check on process state or variables; skip N blocks if false |
| 🔔 Notify | Show a desktop notification mid-workflow |

### Workflow System
- Create multiple named workflows (rename, duplicate, delete)
- Each workflow is an ordered sequence of blocks
- Assign custom keyboard shortcuts per workflow
- Enable/disable individual blocks
- Reopen the last workflow file automatically on startup

### Variables & Data Flow
- Every run gets a shared variable context passed between blocks
- HTTP Request saves its response body to a variable (e.g. `http_response`)
  plus the status code (`http_response_status`)
- Use `{{variable_name}}` in URLs, bodies, text, notifications, paths and
  window titles — unknown variables are left untouched (JSON-safe)
- Condition blocks can branch on variables: equals / not equals /
  contains / is empty

### Execution Engine
- Runs in a background thread (UI stays responsive)
- Live block highlighting (running → success/error)
- Condition-based block skipping and Loop blocks (repeat N blocks M times)
- Stop button interrupts even long waits instantly
- Color-coded execution log

### File System
- Save all workflows to a single JSON file
- Load and restore complete workflow state
- Dirty-state tracking (warns on unsaved changes)

### Hotkeys
- Record any Ctrl/Shift/Alt + key combination
- Registered globally (works when app is minimized)
- Workflows can be triggered without focusing the app

### System Tray
- Minimize to system tray
- Double-click tray icon to restore
- Tray notification when workflow completes

---

## 🧩 How to Use

### Creating a Workflow
1. Click **+** in the Workflows panel (top-left) → name it
2. Drag action blocks from the **Actions** panel onto the canvas
3. Click a block to edit its properties in the right panel
4. Click **▶ Run** or press the assigned hotkey

### Drag & Drop Reordering
- Drag any block to a new position on the canvas
- Right-click a block for Move Up / Move Down / Delete

### Setting a Hotkey
- Right-click a workflow in the workflow list → **Set Hotkey**
- Click **Record**, press your key combination, click **OK**

### Saving / Loading
- **Save** (top bar) → choose a `.json` file location
- **Load** → pick a previously saved `.json` file
- Subsequent saves update the same file automatically

---

## 🔌 Adding Custom Actions

1. Create a class in `actions/` inheriting `BaseAction`
2. Set class attributes: `ACTION_TYPE`, `ACTION_LABEL`, `ACTION_ICON`, `ACTION_COLOR`
3. Implement `execute()` returning an `ActionResult`
4. Register it: `ActionRegistry.register(MyAction)` in `core/registry.py`
5. Add a properties builder branch in `ui/properties_panel.py`

```python
# Example: actions/my_action.py
from actions.base_action import BaseAction, ActionResult

class TypeTextAction(BaseAction):
    ACTION_TYPE        = "type_text"
    ACTION_LABEL       = "Type Text"
    ACTION_ICON_KEY    = "dot"        # see ui/icons.py for available keys
    ACTION_COLOR       = "#E67E22"
    ACTION_DESCRIPTION = "Type text using the keyboard."

    def _init_params(self):
        self._params = {"text": "", "delay": 0.05}

    def execute(self) -> ActionResult:
        import pyautogui
        text = self.get_param("text", "")
        pyautogui.typewrite(text, interval=self.get_param("delay", 0.05))
        return ActionResult(True, f"Typed: {text[:30]}")
```

> **Tip:** for long-running actions (long waits, polling loops), call
> `self.is_stop_requested()` periodically and return
> `ActionResult(..., cancelled=True)` so the **Stop** button stays responsive.

---

## 🛠 Architecture Notes

### Threading Model
The `WorkflowEngine` moves an `EngineWorker` onto a `QThread`. All UI updates
happen via Qt signals (thread-safe). The engine never touches widgets directly.

### Serialization
Every action implements `to_dict()` / `from_dict()`. `ActionRegistry` maps type
strings → classes, enabling safe JSON round-trips without `eval` or `pickle`.

### Scalability Hooks
- `BaseAction` is abstract — any new action just implements `execute()`
- `ActionRegistry` is the single place to add new block types
- Engine emits granular signals, making it easy to add AI orchestration, loops,
  parallel branches, or remote execution in the future

---

## 🔮 Suggested Future Improvements

| Feature | Notes |
|---------|-------|
| AI Task Block | Send a prompt to an LLM; use response to branch |
| Mouse block | `pyautogui` for clicks and drags |
| Screenshot/OCR block | Capture screen, read text with tesseract |
| Schedule trigger | Run workflows on a cron-like schedule |
| Workflow recorder | Record mouse/keyboard actions → auto-build workflow |
| Plugin system | Load third-party action packs from `plugins/` directory |
| Cloud sync | Save/share workflows to a cloud backend |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `PySide6` | Qt6 GUI framework |
| `psutil` | Process listing and termination |
| `pygetwindow` | Window title lookup and control |
| `keyboard` | Global hotkey registration |

---

*Built with ♥ using Python 3 + PySide6*
