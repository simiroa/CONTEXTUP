# ContextUp GUI Guidelines (v2.0 - Updated Dec 2024)

This document outlines GUI standards for all ContextUp tools, ensuring consistent UX and maintainable code.

---

## 1. Base Classes (gui_lib.py)

### 1.1 BaseWindow
All tools MUST inherit from `BaseWindow` for consistent styling:

```python
from utils.gui_lib import BaseWindow

class MyToolGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="My Tool", width=600, height=500)
        # ...
```

### 1.2 Start Patterns (Robust Input)
Tools should accept a list of files to support multi-selection reliably.

```python
def __init__(self, files_list):
    super().__init__(...)
    # Handle both single path and list
    if isinstance(files_list, (list, tuple)):
        self.files, _ = scan_for_images(files_list)
    else:
        # Fallback for single path
        self.files, _ = scan_for_images([files_list])
```

**Main Block Pattern:**
```python
if __name__ == "__main__":
    if len(sys.argv) > 1:
        anchor = sys.argv[1]
        # Get all selected files via Explorer COM
        from utils.explorer import get_selection_from_explorer
        all_files = get_selection_from_explorer(anchor) or [Path(anchor)]
        
        # ... Mutex check ...
        
        app = MyToolGUI(all_files)
        app.mainloop()
```

**Provides:**
- Unified icon (ContextUp.ico)
- Theme support (Dark/Light/System)
- Standard padding (20px)
- Taskbar icon handling

### 1.2 FileListFrame
For displaying selected files:

```python
from utils.gui_lib import FileListFrame
file_list = FileListFrame(self.main_frame, self.files, height=150)
file_list.pack(fill="x", padx=20, pady=10)
```

### 1.3 ModernInputDialog
For user input prompts:

```python
from utils.gui_lib import ask_string_modern
result = ask_string_modern("Title", "Enter value:", "default")
```

---

## 2. Standard Patterns

### 2.1 Header Pattern
```python
self.add_header(f"Processing {len(self.files)} Files")
```

### 2.2 Progress Pattern
```python
# Create progress bar with status
self.progress = ctk.CTkProgressBar(self.main_frame)
self.progress.pack(fill="x", padx=40, pady=(20, 5))
self.progress.set(0)

self.lbl_status = ctk.CTkLabel(self.main_frame, text="Ready", text_color="gray")
self.lbl_status.pack(pady=(0, 10))
```

### 2.3 Button Group Pattern (Bottom-aligned)
```python
btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
btn_frame.pack(fill="x", padx=20, pady=10)

self.btn_run = ctk.CTkButton(btn_frame, text="Start", command=self.run)
self.btn_run.pack(side="right", padx=5)

ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", 
              border_width=1, border_color="gray", 
              command=self.cancel_or_close).pack(side="right", padx=5)
```

### 2.4 Cancel Pattern (Dec 2024)
For batch operations, implement cancellation support:

```python
def __init__(self, ...):
    self.cancel_flag = False  # Add cancel flag
    # ...

def cancel_processing(self):
    if self.btn_run.cget("state") == "disabled":
        self.cancel_flag = True
        self.lbl_status.configure(text="Cancelling...")
    else:
        self.destroy()

def start_process(self):
    self.cancel_flag = False  # ⚠️ CRITICAL: Reset flag before each run!
    self.btn_run.configure(state="disabled", text="Processing...")
    threading.Thread(target=self.run_process, daemon=True).start()

def run_process(self):
    for i, item in enumerate(self.items):
        if self.cancel_flag:  # Check in loop
            break
        # ... process item
```

> [!CAUTION]
> **Bug Prevention:** Always reset `cancel_flag = False` at the start of `start_process()`, not just in `__init__`. Otherwise, re-running after cancel will immediately exit.

---

## 3. Bug Prevention Checklist

Before committing GUI changes, verify:

1. **Cancel Pattern**: `cancel_flag` reset in `start_*()` method
2. **Widget References**: All widgets assigned to `self.` are accessible
3. **Method Placement**: No methods nested inside others accidentally
4. **Import Test**: Run `python -c "from module import Class; print('OK')"`
5. **Simple Launch Test**: Test with a real file if possible

| Purpose | Widget | Notes |
|---------|--------|-------|
| Size selection | CTkEntry + preset buttons | Custom input support |
| Format selection | CTkComboBox | Dropdown |
| On/Off toggle | CTkCheckBox | For options |
| Mode selection | CTkRadioButton | Mutually exclusive |
| File list | FileListFrame | Scrollable with icons |
| Log output | CTkTextbox | height=150, Consolas font |

---

## 4. Thread Safety

Always use `threading.Thread(daemon=True)` for long operations:

```python
def start_process(self):
    self.btn_run.configure(state="disabled", text="Processing...")
    threading.Thread(target=self.run_process, daemon=True).start()

def run_process(self):
    # ... processing
    # When done, update UI safely:
    self.after(0, lambda: self.btn_run.configure(state="normal"))
```

---

## 5. Quick Reference

```python
# Standard structure
class MyGUI(BaseWindow):
    def __init__(self, target_path):
        super().__init__(title="...", width=600, height=500)
        self.cancel_flag = False
        # Load files, validate, etc.
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        self.add_header("...")  # Header
        # Main controls...
        # Progress bar + status...
        # Button group...
    
    def cancel_processing(self): ...
    def start_process(self): ...
    def run_process(self): ...
    def on_closing(self): self.destroy()

### 2.5 Tabular Layouts (Grid vs Pack)
For lists with multiple columns (e.g., Checkbox | Name | Option | Button):

*   **DON'T** use `pack()` with predefined `width` or `pack_propagate(False)` roughly. It causes alignment issues when text length varies or when mixing with headers.
*   **DO** use `grid()` with strict `minsize` for both Header and Rows.
*   **DO** define a shared `COL_CONFIG` dictionary to act as a **Single Source of Truth** for column widths.

**Example (Robust Alignment):**

```python
COL_CONFIG = {0: 40, 1: 300, 2: 100} # Single Source of Truth

class Row(ctk.CTkFrame):
    def __init__(self, ...):
        # Apply config to every row
        for col, width in COL_CONFIG.items():
            self.grid_columnconfigure(col, minsize=width)
            
        self.chk.grid(row=0, column=0)
        self.lbl.grid(row=0, column=1)

# In Main Window (Header)
table_header = ctk.CTkFrame(...)
for col, width in COL_CONFIG.items():
    table_header.grid_columnconfigure(col, minsize=width)

ctk.CTkLabel(table_header, text="Use").grid(row=0, column=0)
```

**Note:** For variable-width content (filenames) inside a fixed column, wrap the label in a container frame with `pack_propagate(False)` to physically prevent expansion:
```python
self.frame_source = ctk.CTkFrame(self, width=COL_CONFIG[1], height=28)
self.frame_source.pack_propagate(False) # Strict lock
self.lbl_source = ctk.CTkLabel(self.frame_source, ...)
self.lbl_source.pack(fill="both")
```
```

### 2.6 Rigid Layout Rule (Footer First)
To prevent the footer from being pushed off-screen by expanding content:

**Pack Order MUST be:**
1.  **Footer**: `pack(side="bottom", fill="x")` **FIRST**.
2.  **Header**: `pack(side="top", fill="x")` **SECOND**.
3.  **Body**: `pack(side="top", fill="both", expand=True)` **LAST**.

```python
def create_widgets(self):
    # 1. Footer (Bottom) - FIRST
    footer = ctk.CTkFrame(self.main_frame)
    footer.pack(side="bottom", fill="x")
    
    # 2. Header (Top) - SECOND
    self.add_header(...)
    
    # 3. Body (Middle) - LAST
    body = ctk.CTkFrame(self.main_frame)
    body.pack(side="top", fill="both", expand=True)
```
