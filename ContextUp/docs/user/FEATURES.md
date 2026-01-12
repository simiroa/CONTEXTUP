# ✨ ContextUp 상세 기능 가이드

> **[At a Glance]**
> ContextUp은 윈도우 우클릭 메뉴를 통해 파일 관리, 미디어 편집, 그리고 최첨단 로컬 AI 기능을 즉각적으로 제공하는 생산성 플랫폼입니다.
> - **Core**: 매니저, 트레이 앱, 퀵 메뉴를 통한 통합 제어 인터페이스 제공
> - **Tiers**: 무설치 수준의 1단계부터 고성능 GPU AI 모델을 구동하는 3단계까지 선택적 설치 가능
> - **DCC Link**: 블렌더, ComfyUI 등 전문 도구와의 고도화된 워크플로우 연동 지원

> [!TIP]
> 각 기능의 상세 사용법은 **영문 이름**을 클릭하여 매뉴얼을 확인하세요.

---

## 🖥️ Core Interface (관리 인터페이스)
**ContextUp의 모든 동작을 제어하는 3대 핵심 사용자 환경입니다.**

| 구성 요소 | 주요 기능 | 상세 설명 |
| :--- | :--- | :--- |
| [**Manager**](../manuals/ko/manager.md) ⚙️ | 통합 제어판 | 메뉴 항목 커스터마이징, API 키 관리, 외부 도구 경로 설정 및 시스템 최적화 |
| **Tray Agent** 🛠️ | 상시 가동 엔진 | 전역 단축키 감지, 실시간 메뉴 동기화 및 백그라운드 서비스 모니터링 |
| **Quick Menu** ⚡ | 고속 팝업 창 | 작업 중인 파일 형식에 맞춤화된 도구를 소환하는 컨텍스트 기반 런처 (`Ctrl+Shift+C`) |
| [**Monitor Widget**](../manuals/ko/monitor_widget.md) 📊 | 시스템 모니터 | CPU, GPU, RAM, 네트워크, 서버 현황을 실시간으로 표시하는 데스크탑 위젯 |

---

## 🟢 1단계: 최소 설치 (Minimal) - 약 +15개 기능
**시스템 기본 라이브러리(Pillow, pywin32)만 사용하는 초경량 필수 유틸리티입니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기능 소개 | 비고 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **System** | <img src="../../assets/icons/icon_sys_finder.png" width="24"> | [**Finder**](../manuals/ko/finder.md) | 파인더 | 고속 해싱으로 중복 및 대용량 파일을 정교하게 탐색 및 관리 | `Alt+Space` |
| **System** | <img src="../../assets/icons/icon_sys_clean_empty_dir.png" width="24"> | [**Clean Folder**](../manuals/ko/clean_empty_folders.md) | 빈 폴더 정리 | 비어있는 모든 하위 디렉토리를 탐색하여 불필요한 구조 일괄 제거 | 기본 내장 |
| **System** | <img src="../../assets/icons/icon_sys_move_to_new_folder.png" width="24"> | [**Move to New**](../manuals/ko/move_to_new_folder.md) | 새 폴더로 이동 | 선택된 항목들을 담을 새 폴더를 즉시 생성 및 안전하게 이동 | Shell API |
| **System** | <img src="../../assets/icons/icon_sys_batch_rename.png" width="24"> | [**Batch Rename**](../manuals/ko/batch_rename.md) | 일괄 이름 변경 | 수백 개의 파일명을 규칙에 따라 일괄 변경 | 기본 내장 |
| **System** | <img src="../../assets/icons/icon_sys_symlink.png" width="24"> | [**Create Symlink**](../manuals/ko/create_symlink.md) | 심볼릭 링크 | 파일/폴더에 대한 심볼릭 링크 생성 | 관리자 권한 |
| **Clipboard** | <img src="../../assets/icons/icon_sys_open_path.png" width="24"> | [**Open Path**](../manuals/ko/open_from_clipboard.md) | 경로 열기 | 클립보드에 복사된 경로를 감지하여 해당 위치를 즉시 탐색기로 이동 | `Ctrl+Alt+V` |
| **Clipboard** | <img src="../../assets/icons/icon_sys_save_clip_img.png" width="24"> | [**Save Clip Img**](../manuals/ko/save_clipboard_image.md) | 이미지 저장 | 클립보드의 이미지 데이터를 감지하여 즉시 파일(PNG)로 저장 | Pillow |
| **Clipboard** | <img src="../../assets/icons/icon_sys_copy_unc_path.png" width="24"> | [**Copy UNC Path**](../manuals/ko/copy_unc_path.md) | UNC 경로 복사 | 네트워크 공유 폴더 호환 형식(`\\Server\Share\...`)으로 경로 복사 | Tray |
| **Clipboard** | <img src="../../assets/icons/icon_sys_move_to_new_folder.png" width="24"> | [**Paste to Folder**](../manuals/ko/clipboard_to_new_folder.md) | 붙여넣어 생성 | 클립보드에 있는 파일들을 포함하는 새 폴더를 현재 위치에 즉시 생성 | Shell |
| **Clipboard** | <img src="../../assets/icons/icon_sys_copy_my_info.png" width="24"> | [**Copy My Info**](../manuals/ko/copy_my_info.md) | 내 정보 복사 | 자주 사용하는 텍스트 정보를 등록하고 빠르게 복사 | 트레이 |
| **Document** | <img src="../../assets/icons/icon_sys_pdf_merge.png" width="24"> | [**PDF Merge**](../manuals/ko/pdf_merge.md) | PDF 병합 | 여러 개의 PDF 문서를 하나의 무결성 있는 파일로 통합 | pypdf |
| **Document** | <img src="../../assets/icons/icon_sys_pdf_split.png" width="24"> | [**PDF Split**](../manuals/ko/pdf_split.md) | PDF 분할 | 다페이지 PDF를 개별 페이지 또는 지정 범위로 정밀 분할 | pypdf |
| **Tools** | <img src="../../assets/icons/icon_video_downloader.png" width="24"> | [**Video Downloader**](../manuals/ko/youtube_downloader.md) | 영상 다운로드 | 스트리밍 영상 및 음원을 로컬 환경으로 저장 | yt-dlp |


---

## 🟡 2단계: 표준 설치 (Standard) - 약 +25개 기능
**미디어 편집(FFmpeg, OpenCV)과 API AI를 활용한 생산성 강화 환경입니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기능 소개 | 비고 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Image** | <img src="../../assets/icons/icon_image_format_convert.png" width="24"> | [**Img Convert**](../manuals/ko/image_convert.md) | 이미지 변환 | 수십 종의 특수 포맷 및 최신 포맷을 고화질 무손실 상호 변환 | OpenCV |
| **Image** | <img src="../../assets/icons/icon_image_compare.png" width="24"> | [**Img Compare**](../manuals/ko/image_compare.md) | 이미지 비교 | 두 이미지를 나란히 비교하거나 차이점 하이라이트 | Pillow |
| **Image** | <img src="../../assets/icons/icon_image_metadata.png" width="24"> | [**Img Metadata**](../manuals/ko/image_metadata.md) | 메타데이터 편집 | 이미지 EXIF/IPTC 메타데이터 조회 및 편집 | piexif |
| **Image** | <img src="../../assets/icons/icon_image_resize.png" width="24"> | [**Resize POT**](../manuals/ko/resize_power_of_2.md) | 2의 거듭제곱 리사이즈 | 게임 엔진 최적화용 2^n 크기로 리사이즈 | Pillow |
| **Image** | <img src="../../assets/icons/icon_image_vectorizer.png" width="24"> | [**Vectorizer**](../manuals/ko/rigreader_vectorizer.md) | 벡터화 | 이미지를 SVG 벡터로 정밀 변환 | vtracer |
| **Video** | <img src="../../assets/icons/icon_video_convert.png" width="24"> | [**Vid Convert**](../manuals/ko/video_convert.md) | 영상 변환 | 비트레이트 제어 및 코덱 변환을 통한 용량/호환성 최적화 | FFmpeg |
| **Video** | <img src="../../assets/icons/icon_video_frame_interp.ico" width="24"> | [**Interp 30fps**](../manuals/ko/interpolate_30fps.md) | 30fps 보간 | 저프레임 영상을 30fps로 부드럽게 변환 | FFmpeg |
| **Video** | <img src="../../assets/icons/icon_video_audio_tools.ico" width="24"> | [**Extract Audio**](../manuals/ko/extract_audio.md) | 오디오 추출 | 영상에서 오디오 트랙만 원본 무손실 또는 MP3로 추출 | FFmpeg |
| **Video** | <img src="../../assets/icons/icon_video_mute.ico" width="24"> | [**Remove Audio**](../manuals/ko/remove_audio.md) | 오디오 제거 | 영상의 오디오 트랙을 제거하여 무음 영상 생성 | FFmpeg |
| **Video** | <img src="../../assets/icons/icon_video_proxy.png" width="24"> | [**Create Proxy**](../manuals/ko/create_proxy.md) | 프록시 생성 | 편집용 저해상도 프록시 파일 생성 | FFmpeg |
| **Audio** | <img src="../../assets/icons/icon_audio_convert.png" width="24"> | [**Audio Convert**](../manuals/ko/audio_convert.md) | 오디오 변환 | MP3, WAV, FLAC 등 오디오 포맷 상호 변환 | FFmpeg |
| **Audio** | <img src="../../assets/icons/icon_audio_normalize.png" width="24"> | [**Normalize Volume**](../manuals/ko/normalize_volume.md) | 볼륨 정규화 | 오디오 파일 볼륨 평준화 | FFmpeg |
| **Sequence** | <img src="../../assets/icons/icon_seq_video.png" width="24"> | [**Seq to Video**](../manuals/ko/sequence_to_video.md) | 시퀀스→비디오 | 이미지 시퀀스를 비디오로 인코딩 | FFmpeg |
| **Sequence** | <img src="../../assets/icons/icon_seq_analyze.png" width="24"> | [**Seq Analyze**](../manuals/ko/sequence_analyze.md) | 시퀀스 분석 | 시퀀스 정보 및 누락 프레임 확인 | 기본 내장 |
| **Tools** | <img src="../../assets/icons/icon_ai_text_lab.ico" width="24"> | [**AI Text Lab**](../manuals/ko/ai_text_lab.md) | 텍스트 연구소 | Gemini/Ollama 기반 텍스트 번역, 정제 및 스타일 변환 | API Key |
| **Tools** | <img src="../../assets/icons/vacance.ico" width="24"> | [**Leave Manager**](../manuals/ko/leave_manager.md) | 휴가 관리 | 연차/휴가 사용 내역을 시각적으로 관리하고 잔여일 계산 | 트레이 전용 |
| **Document** | <img src="../../assets/icons/icon_doc_convert.png" width="24"> | [**Doc Convert**](../manuals/ko/doc_convert.md) | 문서 변환 | PDF를 워드로 변환하거나 이미지/PDF에서 텍스트 추출 | pdf2docx |
| **AI Light** | <img src="../../assets/icons/icon_ai_gemini_vision.png" width="24"> | [**Gemini Tool**](../manuals/ko/gemini_image_tool.md) | Gemini AI 분석 | 클라우드 기반 비전 AI를 활용한 이미지 맥락 분석 및 데이터 추출 | Gemini API |

---

## 🔴 3단계: 전체 설치 (AI Heavy) - 약 +20개 기능
**내장 로컬 AI 엔진(Torch, ONNX)을 구동하여 고부하 작업을 독립적으로 처리합니다.**

| 카테고리 | 아이콘 | 영문 이름 | 한글 이름 | 기술적 소개 | 비고 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **AI Heavy** | <img src="../../assets/icons/icon_image_remove_bg_ai.png" width="24"> | [**BG Removal**](../manuals/ko/image_remove_bg_ai.md) | 배경 제거 | Deep Learning 기반 Salient Object Detection을 통한 정교한 마스킹 | [Rembg](https://github.com/danielgatis/rembg) |
| **AI Heavy** | <img src="../../assets/icons/icon_image_upscale_ai.png" width="24"> | [**AI Upscale**](../manuals/ko/esrgan_upscale.md) | AI 업스케일 | SRGAN 모델을 사용하여 이미지의 고주파 디테일 재구성 및 해상도 복원 | Real-ESRGAN |
| **AI Heavy** | <img src="../../assets/icons/subtitle.png" width="24"> | [**Whisper AI**](../manuals/ko/whisper_subtitle.md) | Whisper 자막 | Robust Speech-to-Text 엔진을 활용한 고정밀 오디오 전사 및 동기화 | Faster-Whisper |
| **AI Heavy** | <img src="../../assets/icons/icon_ai_pbr.png" width="24"> | [**Marigold PBR**](../manuals/ko/marigold_pbr.md) | PBR 맵 생성 | Diffusion 모델 기반 Monocular Depth Estimation을 통한 3D 텍스처 추출 | Marigold |
| **AI Heavy** | <img src="../../assets/icons/icon_audio_separate_stems.png" width="24"> | [**Demucs Stems**](../manuals/ko/demucs_stems.md) | 음원 분리 | Source Separation 기법을 응용하여 오디오 요소를 트랙별로 완전 분리 | Meta Demucs |
| **AI Heavy** | <img src="../../assets/icons/icon_audio_bgm.png" width="24"> | [**Extract BGM**](../manuals/ko/extract_bgm.md) | BGM 추출 | 음성을 제거하고 배경음악만 추출 | Demucs |
| **AI Heavy** | <img src="../../assets/icons/icon_audio_voice.png" width="24"> | [**Extract Voice**](../manuals/ko/extract_voice.md) | 보컬 추출 | 배경음악을 제거하고 보컬만 추출 | Demucs |


---

## 🏗️ DCC & Professional Link - 외부 도구 연동 기능 (약 +10개)
**자동 설치되지 않으며**, 사용자의 PC에 설치된 전문 소프트웨어나 포터블 버전을 연결해야 활성화되는 고사양 기능입니다.

> [!NOTE]
> FFmpeg, Real-ESRGAN, Whisper 등의 핵심 도구와 라이브러리는 **1~3단계 설치 과정에서 자동으로 구성**되므로 별도의 수동 연동이 필요하지 않습니다.

| 카테고리 | 아이콘 | 기능 이름 | 한글 이름 | 연동 필수 도구 | 기능 설명 |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **3D Content** | <img src="../../assets/icons/icon_mesh_remesh_bake.ico" width="24"> | [**Remesh & Bake**](../manuals/ko/blender_bake_gui.md) | 리메쉬 및 베이크 | **Blender** | 블렌더 엔진과 연동하여 고폴리곤 매쉬를 재구축하고 텍스처를 굽습니다. |
| **3D Content** | <img src="../../assets/icons/icon_mesh_convert_format.png" width="24"> | [**Mesh Convert**](../manuals/ko/mesh_convert.md) | 매쉬 변환 전문 | **Blender / Mayo** | FBX, OBJ, GLB 등 복잡한 3D 데이터 포맷 간의 상호 변환을 지원합니다. |
| **3D Content** | <img src="../../assets/icons/icon_3d_mayo.ico" width="24"> | [**Open with Mayo**](../manuals/ko/open_with_mayo.md) | Mayo로 열기 | **Mayo** | 3D CAD 파일(STEP, IGES)을 경량 뷰어인 Mayo로 즉시 엽니다. |
| **3D Content** | <img src="../../assets/icons/icon_3d_lod.png" width="24"> | [**Auto LOD**](../manuals/ko/auto_lod.md) | 자동 LOD | **pymeshlab** | 고해상도 메쉬의 LOD 모델 자동 생성 |
| **3D Content** | <img src="../../assets/icons/icon_3d_cad.png" width="24"> | [**CAD to OBJ**](../manuals/ko/cad_to_obj.md) | CAD → OBJ | **Blender/Mayo** | STEP, IGES 등 CAD 포맷을 OBJ로 변환 |
| **Advanced AI** | <img src="../../assets/icons/icon_video_upscale_ai.ico" width="24"> | [**SeedVR2**](../manuals/ko/seedvr2_upscaler.md) | AI 영상 개선 | **ComfyUI** | ComfyUI 워크플로우를 소환하여 영상 화질을 시네마틱 급으로 향상시킵니다. |
| **Audio Space** | <img src="../../assets/icons/icon_music.ico" width="24"> | [**Creative Audio (ACE)**](../manuals/ko/ace_audio_editor.md) | ACE 오디오 편집 | **ComfyUI** | ComfyUI 기반 오디오 생성/리페인팅 및 고도화된 음성 변조 작업을 지원합니다. |
| **Creative** | <img src="../../assets/icons/icon_art.ico" width="24"> | [**Creative Studio (Z)**](../manuals/ko/creative_studio_z.md) | 크리에이티브 (Z) | **ComfyUI** | Z-Image Turbo를 활용한 초고속 이미지 생성 워크스페이스. |
| **Creative** | <img src="../../assets/icons/icon_art.ico" width="24"> | [**Creative Studio (Adv)**](../manuals/ko/creative_studio_advanced.md) | 크리에이티브 (고급) | **ComfyUI** | LoRA 스택, FaceDetailer, SUPIR 등 전문가용 옵션 제공. |
| **Management** | <img src="../../assets/icons/ContextUp.ico" width="24"> | [**Open Web UI**](../manuals/ko/comfyui_dashboard.md) | ComfyUI Web UI | **ComfyUI** | ComfyUI 웹 UI를 열고 서버가 꺼져 있으면 자동으로 시작합니다. |

> [!TIP]
> 위 기능들은 **Manager(매니저) -> 🛠️ Preferences** 메뉴에서 해당 소프트웨어의 실행 파일(.exe) 경로를 연결한 후 사용이 가능합니다.

---

## 📖 전체 매뉴얼 목록

모든 기능의 상세 사용법은 [📂 매뉴얼 폴더](../manuals/ko/)에서 확인할 수 있습니다.
