# Copy My Info Feature

## Overview
The "Copy My Info" feature provides a quick way to copy frequently used personal information (like Email, Phone, IP address) directly from the Windows Context Menu or System Tray, without opening a dedicated application window.

## Components
1.  **SysTray / Context Menu**: Displays the snippets as a cascading menu. Clicking an item copies it to the clipboard.
2.  **Info Manager (`sys_info_manager.py`)**: A modern GUI tool to add, edit, or delete these snippets.

## Usage
-   **Right-Click** any file or empty space -> **ContextUp** -> **Copy My Info**.
-   Hover to see your items. Click to copy.
-   Click **Manage Info...** to open the editor.

## Configuration
-   Items are stored in `config/copy_my_info.json`.
-   This file is **local only** and ignored by version control to protect your privacy.
-   The Manager App automatically creates this file if it's missing.

## Technical Details
-   **Registry Method**: Uses `ExtendedSubCommandsKey` (CLSID-based) to ensure reliable rendering of the nested submenu in Windows Explorer.
-   **Auto-Refresh**: The Manager App triggers a registry refresh immediately upon saving, keeping the context menu in sync.
