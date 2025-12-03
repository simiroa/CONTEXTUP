# Gemini Image Generation Models Reference

Based on documentation: [Gemini Image Generation Docs](https://ai.google.dev/gemini-api/docs/image-generation?hl=ko)

## Available Models

### Gemini 2.5 Flash Image (Nano Banana)
- **Model Name**: `gemini-2.5-flash-image`
- **Purpose**: Speed and efficiency. Optimized for high-volume, low-latency tasks.
- **Resolution**: Generates images at 1024px.
- **Capabilities**: Image generation, image editing.

### Gemini 2.5 Flash (Nano Banana)
- **Model Name**: `gemini-2.5-flash`
- **Purpose**: Multimodal understanding (Image-to-Text).
- **Capabilities**: Captioning, object detection, segmentation, visual Q&A.


### Gemini 3 Pro Image Preview (Nano Banana Pro)
- **Model Name**: `gemini-3.0-pro-image-preview` (Estimated from text, check specific API strings)
- **Purpose**: Professional asset creation, complex instruction following.
- **Features**: Real-world grounding via Google Search, "thinking" process before generation.
- **Resolution**: Up to 4K.

## Usage Notes
- **Image Input**: When performing image editing or analysis, ensure images are passed correctly (e.g., as bytes or base64) to avoid "Unable to process input image" errors.
- **SDK**: Use `google-genai` Python SDK.
