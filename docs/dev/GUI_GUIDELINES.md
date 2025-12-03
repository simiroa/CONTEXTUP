# ContextUp GUI Guidelines

This document outlines the design principles and standards for all Graphical User Interfaces (GUIs) within the ContextUp ecosystem. Adhering to these guidelines ensures a consistent, professional, and user-friendly experience across all tools.

## 1. General Layout

### 1.1. Center Alignment
*   **Principle**: All primary interface elements should be visually centered within their containers.
*   **Implementation**:
    *   Use `pack(expand=True)` or centered `grid` columns/rows to ensure content floats in the center of the window or frame.
    *   Avoid left-justified layouts for main content areas unless specifically required for lists or data tables.

### 1.2. Window Resizing
*   **Principle**: Windows must resize gracefully.
*   **Implementation**:
    *   Central elements should maintain their centered position during resize.
    *   Use `sticky="ew"` (East-West) for input fields that should expand, but keep the container centered.

## 2. Components

### 2.1. Action Buttons
*   **Location**: Bottom of the window or form.
*   **Alignment**: **Centered**.
*   **Grouping**:
    *   Primary Action (e.g., "Generate", "Run") and Secondary Action (e.g., "Cancel") should be grouped together.
    *   Use a transparent frame to hold buttons and center that frame.
*   **Styling**:
    *   Primary Button: Prominent color (e.g., Blue), bold text, larger height (e.g., 40px).
    *   Secondary Button: Transparent or neutral color, standard height.

### 2.2. Option Groups (Tabs/Frames)
*   **Internal Layout**: Content within tabs (e.g., "LOD Chain", "Remesh") should be centered.
*   **Labels**: Section headers and labels should be aligned relative to their input fields but the whole group should be centered.

### 2.3. Status & Feedback
*   **Status Text**: Displayed near the action buttons, center-justified.
*   **Progress Bars**: Full width or centered, placed immediately above or below the status text.

## 3. Theme & Styling

*   **Framework**: `customtkinter` is the standard library.
*   **Mode**: Dark mode is the default.
*   **Colors**:
    *   Background: Default Dark.
    *   Accents: Standard Blue for primary actions.
    *   Text: White/Gray for readability.

## 4. Example Implementation (Python/CustomTkinter)

```python
# Centering a button group at the bottom
btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
btn_frame.pack(side="bottom", fill="x", padx=5, pady=10)

# Inner frame for centering
btn_inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
btn_inner.pack(expand=True)

ctk.CTkButton(btn_inner, text="Cancel", ...).pack(side="left", padx=10)
ctk.CTkButton(btn_inner, text="Action", ...).pack(side="left", padx=10)
```
