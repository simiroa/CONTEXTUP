# ComfyUI Tool Development Guide

## Overview
This document outlines the standard patterns and best practices for developing ComfyUI-integrated GUIs in ContextUp. Follow these guidelines to minimize token usage and avoid common errors.

## Key Components

### 1. Client (`ComfyUIManager`)
Located at: `src/manager/helpers/comfyui_client.py`
-   **Purpose**: Manages the ComfyUI process (start/check) and API communication.
-   **Usage**:
    ```python
    from manager.helpers.comfyui_client import ComfyUIManager
    
    client = ComfyUIManager()
    if not client.start():
        # Handle start failure
    outputs = client.generate_image(workflow_json) # Returns dict {node_id: [ImageObjects]}
    ```

### 2. Workflow Utilities (`workflow_utils`)
Located at: `src/features/comfyui/workflow_utils.py`
-   **Purpose**: Helper functions to manipulate workflow JSONs.
-   **Key Functions**:
    -   `load_workflow(path)`: Loads JSON file.
    -   `update_node_value(workflow, node_id, input_key, value)`: Updates `inputs` dict safely.
    -   `set_seed(workflow, seed)`: Updates all known seed fields.

## Workflow Formats (Critical)

ComfyUI uses two distinct JSON formats. **The API (`generate_image`) ONLY accepts API Format.**

### 1. Saved Format (`"nodes": [...]`)
-   Produced when you "Save" a workflow in the ComfyUI browser interface.
-   Structure: Contains visual info (pos, size) and values in `widgets_values`.
-   **Problem**: Cannot be sent to API directly.
-   **Solution**: Must be converted to API format.
-   **Conversion Logic**: Use `z_image_turbo_gui.convert_to_api_format` logic or similar. Map `widgets_values` to `inputs`.

### 2. API Format (Root is Dict of IDs)
-   Produced when you use "Export (API)" or convert via script.
-   Structure: `{"node_id": {"inputs": {...}, "class_type": "..."}}`.
-   **Preferred**: If possible, save workflows in API format to avoid runtime conversion.

## Development Patterns

### GUI Integration
1.  **Inherit BaseWindow**: Use `src.utils.gui_lib.BaseWindow`.
2.  **Threaded Execution**: Always run `client.generate_image` in a separate `threading.Thread` to keep GUI responsive.
3.  **Local Output**: Save generated PIL images to a local `outputs/` folder immediately for persistence.

### Verification Script Standard
Always create a headless verification script (`dev/scripts/verify_feature.py`) before full GUI testing.
1.  **Format Check**: Detect if `nodes` list exists and call conversion logic.
2.  **Backend Test**: Run `client.generate_image` to ensure ComfyUI accepts the payload.
3.  **Output Confirmation**: Check `tools/ComfyUI/ComfyUI/output` for the generated file.

### Auto-Conversion Pattern (Recommended)
Embed this logic in your GUI/Script to handle user-saved workflows robustly:
```python
if "nodes" in workflow:
    workflow = self.convert_to_api_format(workflow)
```
This allows you to update the `assets/workflows` file directly from ComfyUI "Save" button without manual JSON editing.

## Common Configs & Node IDs
When copying workflows, **Node IDs change**. Always verify IDs in the target JSON file.
-   **CLIPTextEncode**: Usually has input `text`.
-   **KSampler**: Inputs `seed`, `steps`, `cfg` (in API format).
-   **EmptyLatent**: Inputs `width`, `height`, `batch_size`.
