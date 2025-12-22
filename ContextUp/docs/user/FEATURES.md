# ✨ ContextUp Features

All available tools organized by category with brief usage guides.

---

## 🖼️ Image

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Image Convert** | Pillow | JPG, PNG, WEBP, TIF, TGA, BMP, EXR, HDR, ICO, DDS, HEIC, AVIF, RAW 포맷 변환 | 이미지 우클릭 → Image Convert |
| **Resize PoT** | Pillow | 2의 거듭제곱 크기로 리사이즈 (게임 텍스처용) | 이미지 우클릭 → Resize Power of 2 |
| **EXR Merge** | OpenEXR | 여러 이미지를 멀티채널 EXR로 병합 | 이미지 다중선택 → Merge to EXR |
| **EXR Split** | OpenEXR | EXR 채널을 개별 이미지로 분리 | EXR 파일 우클릭 → Split EXR |
| **Texture Packer** | Pillow | ORM 맵 패킹 (Occlusion/Roughness/Metallic) | 이미지 3개 선택 → Texture Packer |
| **Normal Flip** | Pillow | DirectX ↔ OpenGL 노말맵 변환 | 노말맵 우클릭 → Flip Normal Y |
| **Image Compare** | OpenCV | 두 이미지 간의 차이 분석 및 시각화 (EXR 지원) | 이미지 우클릭 → Image Compare |

---

## 🎞️ Sequence

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Arrange** | Python | 이미지 시퀀스를 폴더별로 자동 정리 | 폴더 우클릭 → Arrange Sequence |
| **Find Missing** | Python | 시퀀스 누락 프레임 탐지 | 폴더 우클릭 → Find Missing Frames |
| **To Video** | FFmpeg | 이미지 시퀀스를 MP4/MOV로 변환 | 폴더 우클릭 → Sequence to Video |
| **Renumber** | Python | 시퀀스 번호 재정렬 (시작번호, 간격, 패딩) | 폴더 우클릭 → Renumber Sequence |
| **Analyze** | Python | 시퀀스 정보 분석 (프레임 수, 해상도 등) | 폴더 우클릭 → Analyze Sequence |

---

## � Video

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Video Convert** | FFmpeg | MP4, MOV, AVI, MKV, WebM 포맷 변환 | 비디오 우클릭 → Video Convert |
| **Create Proxy** | FFmpeg | 편집용 저해상도 프록시 생성 | 비디오 우클릭 → Create Proxy |
| **Extract Audio** | FFmpeg | 비디오에서 오디오 추출 | 비디오 우클릭 → Extract Audio |
| **Mute Video** | FFmpeg | 비디오에서 오디오 제거 | 비디오 우클릭 → Mute Video |

---

## 🎵 Audio

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Audio Convert** | FFmpeg | WAV, MP3, OGG, FLAC, M4A 변환 | 오디오 우클릭 → Audio Convert |
| **Normalize Volume** | FFmpeg | 볼륨 레벨 정규화 | 오디오 우클릭 → Normalize Volume |
| **Extract BGM** | Demucs | 배경음악 추출 (보컬 제거) | 오디오 우클릭 → Extract BGM |
| **Extract Voice** | Demucs | 보컬만 추출 | 오디오 우클릭 → Extract Voice |

---

## 📄 Document

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Document Convert** | PyMuPDF | PDF → 이미지/텍스트/마크다운 변환 | PDF 우클릭 → Document Convert |
| **PDF Merge** | pypdf | 여러 PDF를 하나로 병합 | PDF 다중선택 → PDF Merge |
| **PDF OCR** | PaddleOCR | 스캔된 PDF 텍스트 인식 (한/영) | PDF 우클릭 → OCR Document |

---

## 🧊 3D / Mesh

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Auto LOD** | PyMeshLab | 자동 LOD 메시 생성 (25%, 50%, 75%) | 메시 우클릭 → Auto LOD |
| **CAD to OBJ** | Mayo | STEP/IGES/Catia → OBJ 변환 | CAD 파일 우클릭 → CAD to OBJ |
| **Mesh Convert** | Blender | FBX, OBJ, GLB/GLTF 포맷 변환 | 메시 우클릭 → Mesh Convert |
| **Extract Textures** | Blender | 메시에서 텍스처 추출 | 메시 우클릭 → Extract Textures |
| **Remesh & Bake** | Blender | 리메시 및 텍스처 베이크 | 메시 우클릭 → Remesh & Bake |
| **Open with Mayo** | Mayo | Mayo 뷰어로 열기 | 메시 우클릭 → Open with Mayo |

---

## 🤖 AI

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **AI Upscale** | RealESRGAN | 4배 이미지 업스케일 | 이미지 우클릭 → ESRGAN Upscale |
| **SeedVR2 Upscale**| ComfyUI | SeedVR2 모델 기반 영상 업스케일 (GPU 필수) | 비디오 우클릭 → SeedVR2 Upscale |
| **Z Image Turbo** | ComfyUI | 초고속 AI 이미지 생성 (Real-time) | 트레이 → Z Image Turbo |
| **Background Removal** | Rembg | AI 배경 제거 (투명 PNG) | 이미지 우클릭 → Remove Background |
| **Marigold PBR** | Diffusers | Depth/Normal 맵 생성 | 이미지 우클릭 → Marigold PBR |
| **RIFE Interpolation** | RIFE | 프레임 보간 (24fps→60fps) | 비디오 우클릭 → RIFE Interpolation |
| **Whisper Subtitle** | Faster-Whisper | 자동 자막 생성 (.srt) | 비디오 우클릭 → Whisper Subtitle |
| **Demucs Stems** | Demucs | 오디오 스템 분리 (보컬/드럼/베이스) | 오디오 우클릭 → Stem Separation |
| **Gemini Image Tool** | Gemini API | 이미지 분석/설명 생성 | 이미지 우클릭 → Gemini Image Tool |
| **AI Text Refiner** | Gemini/Ollama | 문법 교정, 번역, 프롬프트 최적화 (Think 모드 지원) | 퀵 메뉴/트레이 → AI Text Refiner |
| **PaddleOCR** | PaddleOCR | 이미지/PDF 텍스트 인식 (한/영) | 이미지/PDF 우클릭 → PaddleOCR |

---

## 🛠️ Tools

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **YouTube Downloader** | yt-dlp | YouTube 비디오/오디오 다운로드 | 트레이 → YouTube Downloader |
| **RT Translator** | NLLB | 오프라인 번역기 (항상 위) | 트레이 → RT Translator 또는 `Ctrl+Alt+T` |
| **Vacance Manager** | - | 휴가 관리 (연차/대체휴가/병가 추적) | 트레이 → Vacance |

---

## 📂 System

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Finder** | Python | 중복 파일 찾기, 대용량 파일 검색 | 트레이 → Finder 또는 `Alt+Space` |
| **Batch Rename** | Python | 일괄 이름 변경 (정규식, 접두사/접미사) | 파일 선택 → Batch Rename |
| **Clean Empty Folders** | Python | 빈 폴더 정리 | 폴더 우클릭 → Clean Empty Folders |
| **Create Symlink** | Python | 심볼릭 링크 생성 | 파일/폴더 우클릭 → Create Symlink |
| **Move to New Folder** | Python | 선택 항목을 새 폴더로 이동 | 파일 선택 → Move to New Folder |
| **Unwrap Folder** | Python | 폴더 내용을 상위로 펼치기 | 폴더 우클릭 → Unwrap Folder |

---

## 📋 Clipboard

| Feature | Engine | Description | Usage |
|---------|--------|-------------|-------|
| **Copy My Info** | Python | 자주 쓰는 정보 관리/복사 (이메일, 전화 등) | 트레이 → Copy My Info |
| **Open from Clipboard** | Python | 클립보드 경로 열기 | `Ctrl+Alt+V` |
| **Copy UNC Path** | Python | 네트워크 경로를 UNC 형식으로 복사 | 파일 우클릭 → Copy UNC Path |
| **Paste to New Folder** | Python | 클립보드 파일을 새 폴더에 붙여넣기 | 바탕화면 우클릭 → Paste to New Folder |

---

## ⌨️ Hotkeys

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+C` | Quick Menu (반투명 팝업) |
| `Ctrl+Alt+V` | 클립보드 경로 열기 |
| `Ctrl+Alt+Shift+F1` | Manager 열기 |
| `Alt+Space` | Finder 오버레이 |
