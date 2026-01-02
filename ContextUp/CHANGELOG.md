# Changelog

All notable changes to ContextUp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [4.0.2] - 2026-01-03

### Image
- **Noise Master Redesign**: 
    - Complete architectural overhaul with clean separation of generation (`generators.py`) and compositing (`engine.py`).
    - Added new pattern types: Gradient (Linear/Radial), Checker, Grid, and Brick.
    - Improved noise generation stability and added safe fallbacks for missing libraries.
    - Modernized UI with ThreadPoolExecutor for smooth, background rendering.
    - Simplified controls and unified coordinate system (Scale/Rotation/Offset).

---

## [4.0.1] - 2025-12-23

### Tools
- AI Text Lab is the current text tool name (formerly AI Text Refiner) and is listed under the Tools category.

### ComfyUI
- Creative Studio (Z/Advanced), SeedVR2, and ACE audio editor entries are available with tray access.
- The Web UI launcher is labeled "Open Web UI".

### Data & Privacy
- Download history is stored in `userdata/download_history.json` and migrated from legacy `config/` and `config/runtime/`.

### Installer
- Migration now includes legacy runtime files (`config/runtime/gui_states.json`, `config/runtime/download_history.json`).

### Maintenance
- Test reports and local history artifacts are ignored to keep repositories clean.

---

## [4.0.0] - 2025-12-22

### 🏗️ Major Structural Reorganization
- **Userdata Separation**: 사용자 데이터(`secrets.json`, `overrides`, `history` 등)를 앱 설정과 완전히 분리하여 `userdata/` 디렉토리에서 관리합니다. 이를 통해 설정 백업 및 Git 관리가 용이해졌습니다.
- **Flattened Config Paths**: 불필요한 디렉토리 계층을 제거했습니다. (`config/menu/categories/` -> `config/categories/`)
- **Centralized Path Management**: `src/core/paths.py`를 도입하여 모든 파일 경로를 중앙에서 관리합니다. 이제 더 이상 코드 내에 하드코딩된 상대 경로 문자열을 사용하지 않습니다.
- **Enhanced Manager UI**: 
    - **Item Editor Upgrade**: `show_in_tray`, `external_tools`, `environment` 등 모든 JSON 필드를 GUI에서 직접 편집할 수 있습니다.
    - **External Tools Visibility**: FFmpeg, Blender 뿐만 아니라 ComfyUI 등의 도구 설치 상태를 모니터링할 수 있는 섹션이 추가되었습니다.

### ✨ New Feature Support
- **ComfyUI Integration**: ComfyUI 설치 여부를 자동으로 감지하며, 전용 업스케일러 도구(`comfyui_upscaler`)를 지원합니다.
- **Sequence Category Tools**: 이미지/영상 시퀀스 정렬, 누락 프레임 확인, 렌더링 분석 등 시퀀스 전문 도구들이 강화되었습니다.

### 🛠️ Fixes & Stability
- **Registry Fix**: 서브메뉴 그룹 생성 시 발생하던 `SubCommands` 속성 오류를 해결하여 컨텍스트 메뉴가 사라지는 문제를 근본적으로 수정했습니다.
- **Migration Logic**: 설치(`install.py`) 시 기존 `config/`에 있던 사용자 파일들을 자동으로 `userdata/`로 이동시키는 마이그레이션 도구를 추가했습니다.

---

## [3.9.0] - 2025-12-20

### 🛡️ Dependency Management System
- **Smart Feature Activation**: 필요한 도구(FFmpeg, Blender 등)나 Python 패키지가 설치되지 않은 경우, 해당 기능이 자동으로 숨김 처리됩니다.
- **Improved Manager UI**: 매니저(Settings)에서 의존성이 누락된 기능은 "⚠️" 아이콘과 함께 비활성화(Disabled) 상태로 표시되어, 왜 기능을 사용할 수 없는지 알기 쉬워졌습니다.
- **Stable Registry Integration**: 레지스트리 메뉴 등록 시점에 의존성을 검사하여, 실행 불가능한 메뉴가 우클릭 메뉴에 남지 않도록 개선했습니다.
- **Config Overhaul**: 내부 설정 파일 구조에서 순수 Python 의존성과 외부 도구(External Tools)를 명확히 분리하여 관리 효율성을 높였습니다.

## [3.8.0] - 2025-12-19

### 🏖️ Vacance Manager (New Feature)
- **휴가 관리 도구**: 연차, 대체휴가, 병가를 한 눈에 관리하는 GUI 도구 추가.
- **Calendar View**: 월별 달력에서 휴가 사용 현황을 직관적으로 확인.
- **Data Management**: 휴가 기록 가져오기/내보내기(JSON) 지원.
- **i18n Support**: 앱 전체 언어 설정(한국어/영어)에 따른 동적 번역 적용.

### 🔧 Install Process Overhaul
- **버그 수정**: `install_packages()` 함수에서 실제 pip 설치 호출이 누락된 치명적 버그 수정.
- **누락 패키지 추가**: `yt-dlp`, `opencv-python`, `pdf2docx`, `pymupdf4llm`, `PyPDF2`, `nllb` 등 6개 패키지 추가.
- **외부 도구 설치 통합**: `setup_tools.py`를 설치 프로세스에 통합하여 FFmpeg, ExifTool, RealESRGAN 자동 다운로드.
- **경로 정리**: 일반 도구(`tools/`) vs AI 바이너리(`resources/bin/`) 경로 분리.

### 📚 Documentation Update
- **FEATURES.md**: 전체 기능을 표 형식으로 재작성, 사용법(Usage) 컬럼 추가.
- **README_KR.md**: 버전 배지 3.8.0 업데이트, Vacance 추가.
- **architecture.md**: `vacance/`, `tools/` 디렉토리 추가.

### 🛠️ Fixes
- **Tray Agent**: `features/{id}/gui.py` 패턴의 패키지형 기능(Vacance 등) 실행 경로 인식 수정.
- **Config**: OCR 엔진을 RapidOCR(ONNX Runtime) 기반으로 전환.

---

## [3.7.0] - 2025-12-18

### ✨ Frosted Glass Quick Menu
- **Visual Upgrade**: Windows DWM API(Acrylic)를 활용한 **Frosted Glass(반투명 블러)** 효과 적용.
- **Modern UI**: CustomTkinter 기반의 다크 테마, 둥근 모서리, 부드러운 호버 효과.
- **Enhanced UX**:
    - **Smart Positioning**: 멀티 모니터 환경에서도 화면 밖으로 나가지 않도록 자동 위치 보정.
    - **Pin & Drag**: 📌 핀 버튼으로 고정하고, 빈 공간을 드래그하여 위치 이동 가능.
    - **Dynamic Loading**: `show_in_tray: true`로 설정된 도구들을 JSON에서 동적으로 로딩.
    - **Compact Design**: 불필요한 헤더를 제거하고 직관적인 아이콘 리스트 형태로 최적화.
    - **Collapsible Info**: "Copy My Info" 메뉴를 접이식으로 변경하여 공간 효율성 증대.

### 🤖 AI Text Refiner
- **Rebrand**: 기존 Grammar Checker를 **AI Text Refiner**로 리브랜딩 및 AI 카테고리로 이동.
- **Engine**: **Gemini 2.5 Flash Lite** 모델 탑재로 더 빠르고 정확한 성능 제공.
- **Style Presets**: 단순 교정 외에 "Professional Email", "Smart Summarize", "Translate (KR/EN/FR)", "Prompt Optimizer" 등 다양한 목적의 프리셋 추가.
- **Safety**: 요청 ID 검증을 통해 이전 요청의 응답이 덮어씌워지는 문제 방지.

### 🛠️ Tools & System
- **RT Translator**: 기존 Translator를 'RT Translator'로 명칭 변경 및 트레이 메뉴 접근성 강화.
- **YouTube Downloader**: 트레이 퀵 메뉴에 추가되어 어디서든 즉시 실행 가능.
- **Tray Agent**: Quick Menu와의 연동성을 강화하고, 안정적인 프로세스 실행(Subprocess) 구조로 개선.

---

## [3.6.0] - 2025-12-18

### ✨ New Features & Updates

#### Tools
- **AI Text Refiner**: 기존 `Grammar Checker`를 **AI Text Refiner**로 전면 개편.
    - **Back-end**: **Google Gemini API** (`gemini-2.5-flash-lite`) 탑재.
    - **Streaming**: 실시간 텍스트 생성(Streaming Output) 지원.
    - **Style Presets**: 단순 문법 교정뿐만 아니라 이메일 작성, 요약, 번역(한/영/불), 프롬프트 최적화(Midjourney/Veo3) 등 다양한 목적의 프리셋 제공.

#### Sequence Category
- **New Category**: 이미지/영상 시퀀스 관련 기능을 별도의 "Sequence" 카테고리로 분리.
- **Renamed Tools**: 직관성을 위해 도구 ID와 이름 변경 (`arrange_sequences` -> `sequence_arrange`, `renumber_sequence` -> `sequence_renumber` 등).

#### Rename Category Merge
- **Merged**: `Rename` 카테고리가 `System` 카테고리로 통합됨.
- **Adjustment**: `Batch Rename` 기능이 System 카테고리로 이동.

#### 3D & Mesh Tools
- **Blender Integration**: 스크립트 경로 계산 로직 수정 및 Bake GUI 개선.
- **Mayo Tools**: `mayo-conv.exe`와 `mayo.exe` 구분 및 "Open with Mayo", "CAD to OBJ" 기능 안정화.

#### System & GUI
- **Compact Info Manager**: "Copy My Info" 매니저를 더 작고 효율적인 테이블 형태(Compact Mode)로 리디자인.
- **Menu Exposure**: "PDF Merge" 등 일부 기능이 의도치 않은 컨텍스트(바탕화면 등)에 노출되는 문제 수정.
- **Tray & Hotkey**: `reopen_recent` 기능 복구 및 Tray 메뉴 핫키 연동 개선.

### 🛠️ Fixes
- **Gemini Icon Gen**: `gemini-2.5-flash-image` 모델 호환성 수정 및 아이콘 생성 로직 개선.
- **Move to New Folder**: 바로가기(`.lnk`) 파일에 대해 기능이 잘못 동작하는 문제 예외 처리.
- **Unwrap Filters**: `flatte_directory` 시 발생하는 `NameError` 수정 및 메시지 한글화.

---

## [3.5.0] - 2025-12-17

### 📄 Document Converter Overhaul
- **Engine Replacement**: 기존의 무거운 `pdf2image` 및 `Poppler` 의존성을 제거하고, 가볍고 빠른 **`PyMuPDF`** 엔진으로 전면 교체. 설치 복잡도가 획기적으로 낮아짐.
- **GUI 2.0**:
    - **Compact Design**: 불필요한 공백을 제거하고 작고 단단한 UI로 재설계.
    - **Grouped Layout**: 변환 옵션과 추출 옵션을 명확히 구분하여 가시성 향상.
    - **Dynamic Controls**: 이미지 포맷 선택 시 OCR 비활성화, 텍스트 포맷 선택 시 DPI 비활성화 등 스마트한 UI 상태 제어 구현.
- **Enhanced Conversion**:
    - **Advanced Formats**: Markdown (LLM-optimized), Tables to CSV, Metadata Extraction 등 고급 변환 기능 추가.
    - **Robust OCR**: RapidOCR 기반의 강력한 한글 OCR 지원 (스캔된 PDF 대응).
- **UX Improvements**:
    - **No Console Window**: GUI 실행 시 CMD 창이 뜨지 않도록 `pythonw.exe` 및 `CREATE_NO_WINDOW` 플래그 적용.
    - **Separate Pages**: 이미지 변환 시 페이지 분할 여부 선택 가능.

### 🛠️ Improvements
- **Console Hiding**: 모든 GUI 도구(`menu.py` Dispatcher)에 대해 콘솔 창 숨김 처리 표준화.
- **Logging**: GUI 모드에서는 파일 로그만 남기고 콘솔 출력을 억제하여 깔끔한 실행 보장.

### 🐛 Fixes
- **Import Errors**: GUI 모듈 로딩 시 경로 문제로 인한 `ImportError` 해결.
- **Dependency Management**: `requirements.txt`에 누락된 `pymupdf` 추가.

---

### 🚀 Full GPU Optimization
- **Unified GPU Support**: OCR (RapidOCR), Upscale (Torch), Background Removal (ONNX) 모든 AI 엔진이 GPU를 최우선으로 사용하도록 최적화.
- **Improved Installer**: `install.bat` 실행 시 `check_gpu_status.py`가 자동으로 실행되어 GPU 인식 상태를 즉시 점검.
- **Requirements Updated**: `requirements.txt`에 `platform-specific` GPU 라이브러리(`rapidocr-onnxruntime`, `onnxruntime-gpu`) 명시.
- **Standalone Model Manager**: `download_all_models.py`를 통해 모든 AI 모델(Marigold, Upscale, OCR 등)을 한 번에 다운로드 가능.

### 🛠️ Improvements
- **OCR Tool**: 실행 취소(Cancel) 및 결과 바로 열기(Open Result) 버튼 추가.
- **Cleanup**: 불필요한 레거시 스크립트(`install_rife.py` 등) 삭제 및 정리.
- **Documentation**: `INSTALL.md`에 GPU 지원 및 모델 다운로드 가이드 추가.

---

## [3.3.0] - 2024-12-15

### ✨ New Features

#### Theme & Localization Support
- **테마 변경 지원**: Dark / Light / System 테마 선택 가능 (Settings → Appearance)
- **다국어 지원 인프라**: `config/i18n/` 폴더에 `en.json`, `ko.json` 추가
- **i18n 유틸리티**: `utils/i18n.py` - `t()` 함수로 간편한 문자열 로컬라이제이션
- **언어 설정**: Settings에서 English / 한국어 선택 가능

### 🛠️ Fixes & Improvements

#### Settings UI
- **Appearance 섹션 추가**: 테마와 언어를 한 곳에서 관리
- **즉시 테마 적용**: 테마 변경 시 앱 재시작 없이 바로 적용

#### Configuration
- **Order 번호 수정**: `copy_unc_path` (105→905), `clipboard_to_new_folder` (106→906) - Clipboard 카테고리 범위로 이동
- **LANGUAGE 설정 추가**: `settings.json`에 언어 설정 필드 추가

#### GUI Standardization & Rewrite (Phase 5 & 6)
- **Strict Layout Enforcement**: GUI가 잘리는 문제를 방지하기 위해 `image_resize_gui.py`, `video_seq_gui.py` 등을 Rigid Layout(Footer First)으로 전면 재작성.
- **Unified Footer**: 모든 주요 도구(Image, Video, Audio Convert/Resize)의 Footer를 `Progress -> Options -> Actions` 순서로 통일.
- **기능 추가**: 모든 변환 도구에 "Save to New Folder", "Delete Original" 옵션 표준화 적용.
- **Card UI 제거**: `customtkinter` Frame의 불필요한 보더를 제거하여 Flat하고 Clean한 디자인 적용.

#### Stability
- **GUI Launch Fix**: 좀비 프로세스로 인한 Lock 파일 잔존 시 GUI가 아무 반응 없이 꺼지는 문제 해결 (Stale Lock 자동 정리 로직 추가).
- **Indentation Fix**: `image_resize_gui.py`의 컴파일 에러 수정.

#### Infrastructure
- **Maintenance Scripts Reorg**: `tools/` 폴더 내의 유지보수 스크립트들이 `.gitignore`로 인해 추적되지 않던 문제를 해결하기 위해 `dev_scripts/` 디렉토리로 이동 및 분리.

#### Code Quality
- **불완전 주석 수정**: `marigold_gui.py`의 불완전한 주석 정리

---

## [3.2.0] - 2024-12-14

### 🛠️ Fixes & Improvements

#### Frame Interpolation
- **실시간 로그 스트리밍 (Real-time Log Streaming)**: 작업 진행 상황을 실시간으로 확인할 수 없던 문제 해결. 이제 GUI에서 FFmpeg/RIFE 로그가 즉시 표시됩니다.
- **RIFE 엔진 경로 수정**: `bin/rife` 실행 파일을 찾지 못해 FFmpeg 모드로 강제 전환되던 버그 수정. 이제 RIFE NCNN Vulkan이 정상 인식됩니다.
- **안정성 개선**: GUI 초기화 시 `state` 속성 충돌로 인한 크래시(`TypeError`) 해결.

#### System Tools
- **Paste to New Folder**: 클립보드에 있는 파일을 즉시 새 폴더를 생성하여 붙여넣는 기능 추가 (바탕화면 우클릭).
- **Move to New Folder 개선**: 새 창이 뜨지 않도록 개선하고, 폴더 생성 전 이름을 먼저 입력받는 가벼운 방식으로 변경.
- **컨텍스트 메뉴 최적화**: `Copy UNC Path`와 `Finder`가 파일/폴더 선택 시에는 나오지 않고, 바탕화면(빈 공간)에서만 나오도록 정리.
- **레지스트리 안정화**: `Copy My Info` 등 동적 메뉴가 다른 메뉴 항목을 가리는 현상을 방지하기 위해 강제 순서 정렬(9999) 로직 적용.

#### Image Tools
- **EXR Multi-Pass Manager GUI Redesign**:
    - **Smart Naming**: 파일명 공통 부분 자동 제거 로직 적용 (`MyShot_Diffuse` -> `Diffuse`).
    - **Tight Visual**: 불필요한 여백을 제거하고 Tight한 Grid 레이아웃 적용.
    - **칼각 정렬**: Header와 Row의 정렬 오차가 발생하지 않도록 `minsize` 기반의 Strict Grid 시스템 도입.
- **EXR Tools 분리**: 통합되어 있던 EXR Split/Merge 기능을 별도 GUI 도구로 분리하여 사용성 개선.
- **GUI 보호**: 창 높이보다 컨텐츠가 길 경우 실행 버튼이 잘리는 문제를 방지하기 위한 스크롤 옵션 추가.

#### AI Upscale
- **메모리 보호 로직**: 대용량 이미지 처리 시 예상 메모리 사용량을 미리 계산하고 경고 표시.
- **경로 오류 수정**: 출력 경로 생성 로직 개선.

#### GUI Framework
- **CustomTkinter 호환성**: `window.state()` 메서드 쉐도잉 버그 수정 (전체 도구 적용).

## [3.1.0] - 2024-12-12

### 🚀 Performance

대용량 파일 스캔을 위한 Finder 성능 대폭 개선.

### Added
- **xxhash 지원**: MD5 대비 10배 빠른 해시 알고리즘 적용
- **정렬 옵션**: 결과를 Size/Count/Name으로 정렬 가능
- **개별 Open 버튼**: 각 중복 파일에 Open 버튼 추가

### Changed
- **os.scandir 적용**: os.walk 대비 더 빠른 파일 탐색
- **파일 stat 캐싱**: 중복 I/O 호출 방지
- **PAGE_SIZE 증가**: 50 → 100으로 배치 로딩 개선
- **Selection Tools UI 재설계**: 기능별 시각적 그룹화
- **Smart 모드 활성화**: 버전 파일(v1, v2) 및 시퀀스(001, 002) 자동 감지

---

## [3.0.0] - 2024-12-12

### 🎉 Major Release

완전히 새로운 Manager UI와 성능 최적화, 새로운 기능들이 추가되었습니다.

### Added
- **Copy UNC Path**: 네트워크 경로를 UNC 형식으로 복사
- **DDS 입력 지원**: Image Converter에서 DDS 파일 읽기 지원
- **Quick Menu (Ctrl+Shift+C)**: 어디서든 빠르게 접근 가능한 팝업 메뉴
- **Settings 탭 재설계**: Tray Agent 통합, Quick Menu 인라인 표시
- **Widget Pooling**: Editor 프레임 위젯 재사용으로 렌더링 성능 향상

### Changed
- **Tray Poll Interval**: 5초 → 10초로 변경하여 CPU 사용량 감소
- **Resize Debounce**: 메인 창 크기 조정 시 150ms 딜레이 적용
- **Scroll Freeze**: 에디터 리스트 갱신 시 깜빡임 방지
- **아이콘 재생성**: 59개 아이콘 전체 재생성 (Soft Metal C4D 스타일)

### Removed
- **MoviePy 의존성**: FFmpeg로 충분히 처리되어 제거
- **불필요한 디버그 로그**: 오래된 로그 파일 정리

### Fixed
- Quick Menu와 Tray Menu 항목 동기화
- "Reopen Last Closed Folder" Quick Menu에서 동작하지 않던 문제
- "Open Folder from Clipboard" agent=None 에러 수정

---

## [2.x.x] - Previous Versions

이전 버전 기록은 Git 히스토리를 참조해 주세요.

---

## Categories

- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련
