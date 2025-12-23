# ComfyUI Tool Development Guide

## Overview
This document outlines the standard patterns and best practices for developing ComfyUI-integrated GUIs in ContextUp. Follow these guidelines to avoid common errors and keep UX consistent.

## Key Components

### 1. Service (ComfyUIService)
Located at: `src/manager/helpers/comfyui_service.py`
- **Purpose**: Start/attach to ComfyUI, detect active port, manage logs.
- **Usage**:
```python
from manager.helpers.comfyui_service import ComfyUIService

service = ComfyUIService()
ok, port, started = service.ensure_running(start_if_missing=True)
```

### 2. Client (ComfyUIManager)
Located at: `src/manager/helpers/comfyui_client.py`
- **Purpose**: API communication (prompt queue, history, output).
- **Usage**:
```python
from manager.helpers.comfyui_client import ComfyUIManager

client = ComfyUIManager()
client.set_active_port(port)
images = client.generate_image(workflow_json)
```

### 3. Base GUI (ComfyUIFeatureBase)
Located at: `src/features/comfyui/base_gui.py`
- **Purpose**: Starts ComfyUI in the background, exposes `get_server_url()`, and adds a status bar.
- **Usage**:
```python
class MyComfyTool(ComfyUIFeatureBase):
    def _on_server_ready(self):
        ...
```

### 4. Workflow Utilities (`workflow_utils`)
Located at: `src/features/comfyui/workflow_utils.py`
- **Key Functions**: `load_workflow`, `update_node_value`, `find_node_by_class`, `set_seed`, `get_workflow_path`.

### 5. Workflow Wrappers (Creative Studio)
Located at: `src/features/comfyui/core/wrappers.py`
- Use `BaseWorkflowWrapper` to map UI inputs to workflow JSON, and optional Saved-format conversion.

## Workflow Formats (Critical)

ComfyUI uses two distinct JSON formats. The API only accepts API Format.

### 1. Saved Format (`"nodes": [...]`)
- Produced by "Save" in the ComfyUI Web UI.
- Contains node positions and `widgets_values`.
- Not accepted by the API.
- Convert to API format or use wrapper-specific conversion (e.g., `ACEStepBaseWrapper._dynamic_convert` or `ZImageTurboGUI._convert_to_api`).

### 2. API Format (root is dict of IDs)
- Produced by "Save (API)" or "Export (API)".
- Structure: `{"node_id": {"inputs": {...}, "class_type": "..."}}`.
- Preferred for all shipped workflows.

## Development Patterns

### Dynamic Port Usage (Critical)
Never hardcode `http://127.0.0.1:8188`.
- Use `ComfyUIService.ensure_running()` and set the port on the client.
- Or use `self.get_server_url()` from `ComfyUIFeatureBase`.

### GUI Integration
1. Inherit `ComfyUIFeatureBase` (or `BaseWindow` for headless tools).
2. Run `client.generate_image` in a background thread to keep the GUI responsive.
3. Save outputs explicitly (e.g., `Path.home()/Pictures/ContextUp_Exports`) or rely on `SaveImage` nodes in the workflow.

### UX Expectations
- Provide an "Open Web UI" button that opens `get_server_url()` for advanced inspection.
- Optional: use `utils.ai_helper.refine_text_ai` to polish prompts or lyrics.

### Verification Script Standard
Create a headless verification script before full GUI testing:
1. Ensure ComfyUI is running via `ComfyUIService`.
2. Load workflow JSON and convert if the Saved format is detected.
3. Call `client.generate_image` to confirm API acceptance.
4. Check `tools/ComfyUI/ComfyUI/output` for generated files (if workflow writes files).

### Auto-Conversion Pattern (Recommended)
Embed Saved-format detection to avoid manual JSON conversion:
```python
if "nodes" in workflow:
    workflow = convert_saved_to_api(workflow)  # wrapper or tool-specific conversion
```
Use wrapper conversion patterns from `src/features/comfyui/core/wrappers.py` when possible.

## Advanced: Workflow Wrapper & Preset System

The Creative Studio uses a wrapper architecture to map UI inputs to workflow JSONs.

### 1. Create a Wrapper Class
Define a new class in `src/features/comfyui/core/wrappers.py` (or a dedicated file in that directory) that inherits from `BaseWorkflowWrapper`.

```python
class FluxWorkflowWrapper(BaseWorkflowWrapper):
    def __init__(self):
        super().__init__(
            "Flux.1 Pro (Standard)",
            "High-fidelity generation using Flux.1 model.",
            "assets/workflows/flux/pro_standard.json"
        )

    def get_ui_definition(self):
        return [
            WorkflowWidgetDef("prompt", "text", "Positive Prompt"),
            WorkflowWidgetDef("guidance", "slider", "Guidance Scale", 3.5, {"from": 1, "to": 10, "res": 0.1}),
            WorkflowWidgetDef("steps", "slider", "Sampling Steps", 20, {"from": 1, "to": 50})
        ]

    def apply_values(self, wf, val):
        if "6" in wf: wf["6"]["inputs"]["text"] = val.get("prompt", "")
        if "12" in wf: wf["12"]["inputs"]["guidance"] = val.get("guidance", 3.5)
        return wf
```

### 2. Register the Wrapper
Add your new wrapper to the `WorkflowRegistry` in `src/features/comfyui/core/wrappers.py`.

```python
class WorkflowRegistry:
    def __init__(self):
        self._wrappers = {}
        self.register("z_turbo", ZImageTurboWrapper)
        self.register("flux_pro", FluxWorkflowWrapper)
```

### 3. Workflow JSON Rules (API Format)
- JSON files referenced by `workflow_path` should be in API format.
- Use ComfyUI Developer Mode -> "Save (API)".
- If Saved format is used, add conversion logic in the wrapper.

### 4. Modular Widgets
Available types for `WorkflowWidgetDef`:
- `text`: Multi-line prompt box.
- `slider`: Numeric slider (requires `from`, `to`, `res` in options).
- `image`: File picker (also used for audio inputs).
- `ckpt`: Checkpoint dropdown (auto-populated from server).
- `lora`: Multi-LoRA stacking interface.
- `checkbox`: Boolean toggle.
- `combo`: Predefined options list.
- `item`: Numeric entry field.

## Common Configs & Node IDs
When copying workflows, node IDs change. Always verify IDs in the target JSON.
- `CLIPTextEncode`: usually has input `text`.
- `KSampler`: inputs `seed`, `steps`, `cfg`.
- `EmptyLatent`: inputs `width`, `height`, `batch_size`.
