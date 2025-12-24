# ContextUp (한국어)

![Version](https://img.shields.io/badge/version-4.0.1-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)

**ContextUp**은 Windows 오른쪽 클릭 메뉴를 생산성 허브로 바꿔 주는 올인원 도구입니다.

> [Changelog](../../CHANGELOG.md) | [전체 기능 보기](FEATURES.md)

---

## 주요 기능

| 카테고리 | 예시 기능 |
|----------|-----------|
| AI | 배경 제거, 업스케일(ComfyUI 호환), PBR 생성, 자막 생성, AI Text Lab(Gemini/Ollama), **Creative Studio (Z/Advanced)** |
| 이미지 | 포맷 변환(DDS/EXR/WebP 등), EXR 병합/분리, 텍스처 패커, 2의 거듭제곱 리사이즈 |
| 시퀀스 | 렌더링 시퀀스 정렬, 누락 프레임 탐색, 영상 변환, 분석 및 리넘버링 |
| 비디오 | ProRes 변환, 프록시 생성, 프레임 보간(RIFE), 유튜브 다운로더 |
| 오디오 | 포맷 변환, 보컬/배경 분리, 볼륨 정규화 |
| 3D | Auto LOD, CAD→OBJ, 메시 변환, 텍스처 추출, Blender 연동 |
| 시스템 | 배치 리네임, 내 정보 복사, UNC 경로 복사, 심볼릭 링크, 파일 찾기 |

---

## 🚀 설치 방법 (Installation)

### 요구 사항

| 항목 | 요구 |
|------|------|
| **OS** | Windows 10/11 (64-bit) |
| **Python** | 3.9 ~ 3.12 (설치 스크립트 실행용) |
| **디스크** | 최소 2GB (AI 모델 및 풀 데이터 설치 시 5GB+) |

> 설치 후에는 `tools/python/`에 내장된 Python 3.11을 사용하므로 시스템 환경과 완전히 분리됩니다.

### 1. 설치 및 마이그레이션 (Setup)

최상위 디렉토리에서 `install.bat`을 실행하거나 다음 명령어를 사용하여 설치를 진행하세요. (embedded Python이 없을 때만 시스템 Python이 필요합니다.)
기존 사용자의 경우 설정 파일이 `userdata/` 폴더로 자동 마이그레이션됩니다.

```bash
python ContextUp/src/setup/install.py
```

### 2. 메뉴 관리 (Manager)

설치가 완료되면 Manager GUI를 통해 메뉴를 레지스트리에 등록/해제할 수 있습니다.

**Manager 실행:**
최상위 폴더의 `manager.bat`을 실행하세요.

**주요 기능:**
- **Refresh Menu**: 현재 설정과 의존성(External Tools)을 체크하여 메뉴를 다시 등록합니다.
- **Item Editor**: 각 기능의 노출 여부, 순서, 아이콘 등을 직접 편집할 수 있습니다.
- **Dependency Scan**: 필요한 외부 도구가 설치되어 있는지 한눈에 확인합니다.

### 3. CLI (Command Line Interface)

명령줄에서도 관리가 가능합니다:
```bash
# 메뉴 등록
ContextUp\tools\python\python.exe ContextUp\manage.py register
# 메뉴 해제
ContextUp\tools\python\python.exe ContextUp\manage.py unregister
```

---

## 제거 (Uninstallation)

```bash
# 메뉴 해제
python ContextUp/manage.py unregister

# (선택) 설치된 도구 삭제
ContextUp\tools\python\python.exe ContextUp\src\setup\uninstall.py
```

---

## 🔧 외부 도구 설정 (External Tools)

일부 고급 기능은 별도 설치가 필요한 외부 도구를 사용합니다.
도구를 `ContextUp/tools/` 폴더에 배치하면 자동으로 인식됩니다.

> **💡 팁**: 용량이 큰 도구(Blender, ComfyUI)는 심볼릭 링크 사용을 권장합니다.

| 도구 | 용도 | 다운로드 |
|------|------|----------|
| **FFmpeg** | 비디오/오디오 변환 | [ffmpeg.org](https://ffmpeg.org/download.html) |
| **Blender** | 3D 메시 변환, LOD | [blender.org](https://www.blender.org/download/) |
| **ComfyUI** | AI 이미지 업스케일 및 생성 | [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI) |
| **Mayo** | CAD 파일(STEP/IGES) 뷰어 | [github.com/fougue/mayo](https://github.com/fougue/mayo/releases) |
| **Real-ESRGAN** | AI 이미지 업스케일 | [github.com/xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN/releases) |

### 설치 경로

```
ContextUp/tools/
├─ ffmpeg/         # ffmpeg.exe, ffprobe.exe
├─ blender/        # blender-x.x.x-windows-x64/
├─ Mayo/           # mayo.exe
├─ realesrgan/     # realesrgan-ncnn-vulkan.exe
└─ ComfyUI/        # (심볼릭 링크 권장)
```

> **⚠️ 참고**: 기능별 필요 도구가 없으면 해당 메뉴 항목이 비활성화됩니다.

---

## 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+Shift+C` | Quick Menu |
| `Ctrl+Alt+V` | 클립보드 경로 열기 |
| `Alt+Space` | Dup Finder (중복 파일 찾기) |
| `Ctrl+Alt+Shift+F1` | Manager 열기 |

---

## 📂 폴더 구조 (Structure)

```
[Root]/
├─ install.bat          # 설치 및 마이그레이션
├─ manager.bat          # 매니저 실행
├─ uninstall.bat        # 제거 스크립트
└─ ContextUp/
   ├─ src/              # 소스 코드 (Core, Features, Manager, Tray)
   ├─ config/           # 앱 기본 설정 (Git 관리)
   │  └─ categories/    # 메뉴 카테고리 설정 (Flattened)
   ├─ userdata/         # 사용자 설정 및 민감 정보 (Git 제외)
   │  ├─ secrets.json   # API 키
   │  ├─ user_overrides.json # 사용자 메뉴 커스텀
   │  ├─ gui_states.json # GUI 상태 저장
   │  ├─ download_history.json # 다운로드 기록
   │  └─ copy_my_info.json # 개인 정보 템플릿
   ├─ tools/            # 내장 Python 및 외부 도구
   ├─ resources/        # AI 모델 및 리소스
   └─ manage.py         # 서버/레지스트리 관리 CLI
```

---

## 감사한 오픈소스

Real-ESRGAN, rembg, Marigold, RIFE, Faster-Whisper, Spleeter, Google Gemini, FFmpeg, Blender, Mayo, PyMeshLab, yt-dlp, CustomTkinter, Pillow 등 많은 프로젝트에 감사합니다.
