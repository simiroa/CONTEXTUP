---
trigger: always
description: Patterns to ignore during debugging and error analysis
---

## Ignore These Patterns - NOT Errors

The following stack traces are **NORMAL BEHAVIOR** and should NOT be treated as errors:

### Tkinter Mainloop
- `File "...\tkinter\__init__.py", line 1599, in mainloop`
- `self.tk.mainloop(n)`

This trace appears when a tkinter GUI application is running normally. It is NOT an error.
Do NOT investigate, debug, or attempt to fix these patterns.

### Python GUI Running Indicators
Any stack trace containing:
- `tkinter\.mainloop`
- `customtkinter` normal execution
- `CTk().mainloop()`

These indicate the GUI is actively running and waiting for user input - this is expected behavior.
