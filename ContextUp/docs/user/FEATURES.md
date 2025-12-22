# ✨ ContextUp 상세 기능 가이드

> **[At a Glance]**
> ContextUp은 윈도우 우클릭 메뉴를 통해 파일 관리, 미디어 편집, 그리고 최첨단 로컬 AI 기능을 즉각적으로 제공하는 생산성 플랫폼입니다.
> - **Core**: 매니저, 트레이 앱, 퀵 메뉴를 통한 통합 제어 인터페이스 제공
> - **Tiers**: 무설치 수준의 1단계부터 고성능 GPU AI 모델을 구동하는 3단계까지 선택적 설치 가능
> - **DCC Link**: 블렌더, ComfyUI 등 전문 도구와의 고도화된 워크플로우 연동 지원

---

## 🖥️ Core Interface (관리 인터페이스)
**ContextUp의 모든 동작을 제어하는 3대 핵심 사용자 환경입니다.**

| 구성 요소 | 주요 기능 | 상세 설명 |
| :--- | :--- | :--- |
| **Manager** ⚙️ | 통합 제어판 | 메뉴 항목 커스터마이징, API 키 관리, 외부 도구 경로 설정 및 시스템 최적화 |
| **Tray Agent** 🛠️ | 상시 가동 엔진 | 전역 단축키 감지, 실시간 메뉴 동기화 및 백그라운드 서비스 모니터링 |
| **Quick Menu** ⚡ | 고속 팝업 창 | 작업 중인 파일 형식에 맞춤화된 도구를 소환하는 컨텍스트 기반 런처 (`Ctrl+Shift+C`) |

---

## 🟢 1단계: 최소 설치 (Minimal) - 약 +15개 기능
**시스템 기본 라이브러리(Pillow, pywin32)만 사용하는 초경량 필수 유틸리티입니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기능 소개 | 비고 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **System** | <img src="../../assets/icons/icon_sys_finder.png" width="24"> | **Finder** | 파인더 | 고속 해싱으로 중복 및 대용량 파일을 정교하게 탐색 및 관리 | `Alt+Space` |
| **System** | <img src="../../assets/icons/icon_sys_clean_empty_dir.png" width="24"> | **Clean Folder** | 빈 폴더 정리 | 비어있는 모든 하위 디렉토리를 탐색하여 불필요한 구조 일괄 제거 | 기본 내장 |
| **System** | <img src="../../assets/icons/icon_sys_move_to_new_folder.png" width="24"> | **Move to New** | 새 폴더로 이동 | 선택된 항목들을 담을 새 폴더를 즉시 생성 및 안전하게 이동 | Shell API |
| **System** | <img src="../../assets/icons/icon_sys_open_recent_folder.png" width="24"> | **Reopen Recent** | 최근 폴더 열기 | 실수로 닫은 탐색기 창을 트레이 기록에서 찾아 즉시 복원 | Tray Agent |
| **Clipboard** | <img src="../../assets/icons/icon_sys_open_path.png" width="24"> | **Open Path** | 경로 열기 | 클립보드에 복사된 경로를 감지하여 해당 위치를 즉시 탐색기로 이동 | `Ctrl+Alt+V` |
| **Clipboard** | <img src="../../assets/icons/icon_sys_save_clip_img.png" width="24"> | **Save Clip Img** | 이미지 저장 | 클립보드의 이미지 데이터를 감지하여 즉시 파일(PNG)로 저장 | Pillow |
| **Document** | <img src="../../assets/icons/icon_sys_pdf_merge.png" width="24"> | **PDF Merge** | PDF 병합 | 여러 개의 PDF 문서를 하나의 무결성 있는 파일로 통합 | pypdf |

---

## 🟡 2단계: 표준 설치 (Standard) - 약 +25개 기능
**미디어 편집(FFmpeg, OpenCV)과 API AI를 활용한 생산성 강화 환경입니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기능 소개 | 비고 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Image** | <img src="../../assets/icons/icon_image_format_convert.png" width="24"> | **Img Convert** | 이미지 변환 | 수십 종의 특수 포맷 및 최신 포맷을 고화질 무손실 상호 변환 | OpenCV |
| **Video** | <img src="../../assets/icons/icon_video_convert.png" width="24"> | **Vid Convert** | 영상 변환 | 비트레이트 제어 및 코덱 변환을 통한 용량/호환성 최적화 | FFmpeg |
| **Video** | <img src="../../assets/icons/icon_video_convert.png" width="24"> | **Interp 30fps** | 30fps 보간 | 저프레임 영상을 30fps로 부드럽게 변환 (Minterpolate) | FFmpeg |
| **Tools** | <img src="../../assets/icons/youtube.png" width="24"> | **YouTube DL** | 유튜브 다운로드 | 스트리밍 영상 및 음원을 로컬 환경으로 무손실 수준 보존 저장 | yt-dlp |
| **Tools** | <img src="../../assets/icons/icon_ai_text.png" width="24"> | **AI Text Lab** | 텍스트 연구소 | LLM(Gemini/Ollama)을 활용한 텍스트 번역, 정제 및 스타일 변환 | API Key |
| **AI Light** | <img src="../../assets/icons/icon_ai_gemini_vision.png" width="24"> | **Gemini Tool** | Gemini AI 분석 | 클라우드 기반 비전 AI를 활용한 이미지 맥락 분석 및 데이터 추출 | Gemini API |

---

## 🔴 3단계: 전체 설치 (AI Heavy) - 약 +20개 기능
**내장 로컬 AI 엔진(Torch, ONNX)을 구동하여 고부하 작업을 독립적으로 처리합니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기술적 소개 | 비고 (Repository) |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **AI Heavy** | <img src="../../assets/icons/icon_image_remove_bg_ai.png" width="24"> | **BG Removal** | 배경 제거 | Deep Learning 기반 Salient Object Detection을 통한 정교한 마스킹 | [Rembg](https://github.com/danielgatis/rembg) / [BiRefNet](https://github.com/ZhengPeng7/BiRefNet) |
| **AI Heavy** | <img src="../../assets/icons/icon_image_upscale_ai.png" width="24"> | **AI Upscale** | AI 업스케일 | SRGAN 모델을 사용하여 이미지의 고주파 디테일 재구성 및 해상도 복원 | [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) |
| **AI Heavy** | <img src="../../assets/icons/subtitle.png" width="24"> | **Whisper AI** | Whisper 자막 | Robust Speech-to-Text 엔진을 활용한 고정밀 오디오 전사 및 동기화 | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) |
| **AI Heavy** | <img src="../../assets/icons/icon_ai_pbr.png" width="24"> | **Marigold PBR** | PBR 맵 생성 | Diffusion 모델 기반 Monocular Depth Estimation을 통한 3D 텍스처 추출 | [Marigold](https://github.com/prs-eth/Marigold) |
| **AI Heavy** | <img src="../../assets/icons/icon_audio_separate_stems.png" width="24"> | **Demucs Stems** | 음원 분리 | Source Separation 기법을 응용하여 오디오 요소를 트랙별로 완전 분리 | [Meta Demucs](https://github.com/facebookresearch/demucs) |
| **AI Heavy** | <img src="../../assets/icons/icon_doc_analyze_ollama.png" width="24"> | **PaddleOCR** | PaddleOCR 인식 | 이미지나 PDF 내의 글자를 고성능 로컬 엔진으로 읽어 텍스트화 | [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) |
| **AI Heavy** | <img src="../../assets/icons/icon_video_frame_interp.png" width="24"> | **RIFE Interp.** | 프레임 보간 | Real-time Intermediate Flow Estimation을 통한 시간적 해상도 확장 | [RIFE-ncnn](https://github.com/nihui/rife-ncnn-vulkan) |

---

## 🏗️ DCC & Professional Link - 외부 도구 연동 기능 (약 +10개)
**자동 설치되지 않으며, 사용자의 PC에 설치된 전문 소프트웨어나 포터블 버전을 연결해야 활성화되는 고사양 기능입니다.**

| 카테고리 | 아이콘 | 기능 이름 | 한글 이름 | 연동 필수 도구 | 기능 설명 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **3D Content** | <img src="../../assets/icons/icon_mesh_remesh_bake.ico" width="24"> | **Remesh & Bake** | 리메쉬 및 베이크 | **Blender** | 블렌더 엔진과 연동하여 고폴리곤 매쉬를 재구축하고 텍스처를 굽습니다. |
| **3D Content** | <img src="../../assets/icons/icon_mesh_convert_format.png" width="24"> | **Mesh Convert** | 매쉬 변환 전문 | **Blender / Mayo** | FBX, OBJ, GLB 등 복잡한 3D 데이터 포맷 간의 상호 변환을 지원합니다. |
| **Advanced AI** | <img src="../../assets/icons/icon_video_upscale_ai.ico" width="24"> | **SeedVR2** | AI 영상 개선 | **ComfyUI** | ComfyUI 워크플로우를 소환하여 영상 화질을 시네마틱 급으로 향상시킵니다. |
| **Advanced AI** | <img src="../../assets/icons/icon_image_upscale_ai.png" width="24"> | **Z Image Turbo** | 초고속 업스케일 | **ComfyUI** | LCM/Turbo 모델을 활용하여 이미지를 즉각적으로 고해상도로 변환합니다. |
| **Advanced AI** | <img src="../../assets/icons/icon_art.ico" width="24"> | **AI Icon Gen** | AI 아이콘 생성기 | **ComfyUI** | 생성형 AI 노드를 실행하여 텍스트로부터 윈도우용 아이콘 파일을 자동 생성합니다. |
| **Audio Space** | <img src="../../assets/icons/icon_music.ico" width="24"> | **ACE Studio** | ACE 오디오 편집 | **ComfyUI** | ComfyUI 기반 오디오 리페인팅 및 고도화된 음성 변조 작업을 지원합니다. |
| **Management** | <img src="../../assets/icons/ContextUp.ico" width="24"> | **Dashboard** | ComfyUI 대시보드 | **ComfyUI** | 워크플로우 관리 및 모델 다운로드 상태를 확인하는 대시보드를 엽니다. |

> [!TIP]
> 위 기능들은 **Manager(매니저) -> 🛠️ Preferences** 메뉴에서 해당 소프트웨어의 실행 파일(.exe) 경로를 연결한 후 사용이 가능합니다.
