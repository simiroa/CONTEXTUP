# ContextUp

![License](https://img.shields.io/badge/license-MIT-blue.svg)

**ContextUp**은 Windows 우클릭 컨텍스트 메뉴를 강력한 생산성 도구로 탈바꿈시키는 확장 프로그램입니다.

AI 기반 이미지/비디오 처리부터 3D 파일 변환, 시스템 유틸리티까지 다양한 기능을 **파일 우클릭**만으로 즉시 사용할 수 있습니다.

> **핵심 철학**: 모든 기능은 **내장 Python(Embedded Python)** 환경에서 실행되어 사용자 시스템에 영향을 주지 않습니다.

---

## 📋 목차
- [기능 목록](#-기능-목록)
- [설치 방법](#-설치-방법)
- [프로젝트 구조](#-프로젝트-구조)
- [설정 및 구성](#%EF%B8%8F-설정-및-구성)
- [개발자 가이드](#-개발자-가이드)
- [라이선스](#-라이선스)

---

## ✨ 기능 목록

### 🤖 AI (인공지능)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **PDF OCR (Paddle)**      | PaddleOCR 기반 PDF 문서 텍스트 추출 (GPU 가속, 자동 회전)            |
| **AI Upscale**              | Real-ESRGAN을 사용한 고해상도 업스케일링 (x4)                        |
| **Remove Background**       | RMBG 2.0 기반 자동 배경 제거                                         |
| **Marigold PBR Gen**        | 단일 이미지에서 Normal, Roughness 등 PBR 맵 생성                     |
| **Frame Interpolation**     | RIFE 기반 프레임 보간 (30fps → 60fps 등)                             |
| **Generate Subtitles**      | Faster-Whisper를 사용한 자동 자막(.srt) 생성                         |
| **Separate Stems (AI)**     | Spleeter 기반 보컬/반주 분리                                         |
| **Prompt Master**           | Ollama Vision을 활용한 이미지 프롬프트 생성                          |
| **[Gemini] Image Tool**     | Google Gemini API 기반 이미지 분석/편집 도구                         |

### 🖼️ Image (이미지)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Resize (Power of 2)**     | 텍스처용 2의 거듭제곱 해상도로 리사이즈 (512x512, 1024x1024 등)       |
| **Merge to EXR**            | 여러 이미지를 다중 레이어 EXR로 병합                                 |
| **Split EXR Layers**        | EXR의 각 레이어를 개별 파일로 분리                                   |

### 🎥 Video (비디오)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Convert Format**          | MP4, MOV, AVI, MKV 등 비디오 포맷 변환                               |
| **Create Proxy Media**      | 편집용 저용량 프록시 생성 (1/2 해상도)                               |
| **Image Sequence to Video** | 이미지 시퀀스를 비디오로 변환                                        |
| **Arrange Image Sequences** | 시퀀스 파일을 자동으로 폴더별 정리                                   |
| **Find Missing Frames**     | 이미지 시퀀스에서 누락된 프레임 검출                                 |
| **Extract Audio**           | 비디오에서 오디오 트랙 추출                                          |
| **Remove Audio Track**      | 비디오에서 오디오 트랙 제거                                          |

### 🎧 Audio (오디오)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Convert Format**          | WAV, MP3, OGG, FLAC 등 오디오 포맷 변환                              |
| **Normalize Volume**        | 볼륨 정규화                                                          |
| **Extract BGM (Filter)**    | FFmpeg 필터 기반 배경음악 추출                                       |
| **Extract Voice (Filter)**  | FFmpeg 필터 기반 보이스 추출                                         |

### 🧊 3D
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Auto LOD Generator**      | PyMeshLab 기반 자동 LOD 생성                                         |
| **Convert CAD to OBJ**      | STEP/IGES CAD 파일을 OBJ로 변환 (Mayo 사용)                          |
| **Convert Mesh Format**     | FBX, OBJ, GLTF, USD 등 Mesh 포맷 변환 (Blender 사용)                 |
| **Extract Textures**        | FBX/GLTF 등에서 내장 텍스처 추출                                     |
| **Open with Mayo**          | Mayo 뷰어로 3D 파일 열기                                             |

### 📄 Document (문서)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Merge PDFs**              | 다중 PDF 파일 병합                                                   |
| **Split PDF**               | PDF 페이지 분할                                                      |

### 📋 Clipboard (클립보드)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Copy My Info**            | 개인 정보(이메일, 전화번호 등) 빠른 복사. 동적 서브메뉴 지원.        |
| **Analyze Clipboard Error** | 클립보드의 오류 메시지를 AI로 분석                                   |
| **Open Path from Clipboard**| 클립보드의 경로로 폴더 열기 (Ctrl+Alt+V)                             |
| **Save Clipboard Image**    | 클립보드 이미지를 현재 폴더에 저장                                   |

### 🏷️ Rename (이름 변경)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **Batch Rename**            | 접두사/접미사 추가, 텍스트 치환 등 일괄 이름 변경                    |
| **Renumber Sequence**       | 이미지 시퀀스 번호 재정렬                                            |

### 🛠️ System (시스템)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **ContextUp Manager**       | 설정 관리, 메뉴 등록/해제, 업데이트 확인                             |
| **Remove Empty Subfolders** | 빈 하위 폴더 자동 삭제                                               |
| **Move into New Folder**    | 선택 파일을 새 폴더로 이동                                           |
| **Unwrap Folder**           | 폴더 내용을 상위로 이동 후 빈 폴더 삭제                              |
| **Reopen Last Closed Folder**| 최근 닫은 폴더 다시 열기 (탐색기 연동)                               |
| **Power Finder**            | 고급 파일 검색 GUI                                                   |
| **Create Symlink Folder**   | 심볼릭 링크 폴더 생성                                                |

### 🔧 Tools (유틸리티)
| 기능                        | 설명                                                                 |
|-----------------------------|----------------------------------------------------------------------|
| **YouTube Downloader**      | yt-dlp 기반 영상/오디오 다운로드                                     |
| **Realtime Translator**     | 실시간 번역기 (구글 번역 API, 클립보드 감지)                         |

---

## 🚀 설치 방법

### 1. 다운로드 및 압축 해제
*   `ContextUp_Release.zip`을 원하는 위치에 압축 해제합니다. (예: `C:\ContextUp`)

### 2. 설치 스크립트 실행
```batch
ContextUp_Install.bat
```
*   내장 Python 환경(`tools/python`)이 자동으로 설치됩니다.
*   모든 필수 라이브러리가 함께 설치됩니다.
*   설치 완료 후 **ContextUp Manager**가 자동으로 실행됩니다.

### 3. 메뉴 등록
*   Manager에서 **"⟳ Refresh Menu"** 버튼을 클릭합니다.
*   이제 Windows 탐색기에서 마우스 우클릭 시 **ContextUp** 메뉴가 표시됩니다.

### 4. 제거
*   `ContextUp_Uninstall.bat`을 실행하면 레지스트리에서 모든 항목이 제거됩니다.
*   프로젝트 폴더를 삭제하면 완전히 제거됩니다.

---

## 📁 프로젝트 구조

```
ContextUp/
├── assets/                 # 아이콘, 이미지 등 리소스
│   └── icons/              # 메뉴 아이콘 (.ico, .png)
│
├── config/                 # 설정 파일
│   ├── menu_categories/    # ★ 기능 정의 JSON (카테고리별 분리)
│   │   ├── ai.json
│   │   ├── image.json
│   │   ├── video.json
│   │   └── ...
│   ├── settings.json       # 사용자 설정
│   └── copy_my_info.json   # 개인정보 스니펫 (Git 미추적)
│
├── src/                    # 소스 코드
│   ├── core/               # 핵심 모듈 (Registry, Config, Logger)
│   ├── manager/            # Manager GUI 소스
│   ├── scripts/            # ★ 기능 스크립트 (sys_*.py, vid_*.py 등)
│   │   └── tray_modules/   # 시스템 트레이 모듈
│   └── utils/              # 유틸리티 함수 (AI Runner, GUI Helper 등)
│
├── tools/                  # 외부 도구 및 내장 Python (Git 미추적)
│   └── python/             # ★ Embedded Python 환경
│
├── docs/                   # 문서
├── tests/                  # 테스트 코드
├── models/                 # AI 모델 (Git 미추적)
│
├── ContextUp_Install.bat   # 설치 스크립트
├── ContextUp_Uninstall.bat # 제거 스크립트
├── ContextUpManager.bat    # Manager 실행기
└── README.md               # 이 문서
```

---

## ⚙️ 설정 및 구성

### 메뉴 카테고리 구조
기능 정의는 `config/menu_categories/` 디렉토리에 **카테고리별 JSON 파일**로 분리되어 있습니다.

**예시: `ai.json`**
```json
{
    "category": "AI",
    "id": "remove_background",
    "name": "Remove Background",
    "icon": "assets/icons/icon_image_remove_bg_ai.ico",
    "types": ".jpg;.jpeg;.png;.webp;.bmp",
    "scope": "file",
    "enabled": true,
    "submenu": "ContextUp",
    "order": 604,
    "gui": false,
    "dependencies": ["rembg", "torch", "Pillow"]
}
```

### 주요 필드 설명
| 필드          | 설명                                                         |
|---------------|--------------------------------------------------------------|
| `id`          | 고유 식별자 (name과 일치하는 snake_case)                     |
| `name`        | 메뉴에 표시되는 이름                                         |
| `types`       | 적용 파일 확장자 (`;`로 구분) 또는 `*` (전체)                |
| `scope`       | `file`, `folder`, `items`, `background`, `both` 중 선택      |
| `submenu`     | 소속 메뉴 (`ContextUp` 또는 `(Top Level)`)                   |
| `enabled`     | 활성화 여부                                                  |
| `order`       | 정렬 순서 (낮을수록 상위)                                    |
| `gui`         | GUI 창 여부 (`true`: 창 열림, `false`: 즉시 실행)            |
| `dependencies`| 필요한 Python 패키지 목록                                    |

---

## 👨‍💻 개발자 가이드

### 새 기능 추가 절차

#### 1. 스크립트 작성
`src/scripts/` 디렉토리에 Python 스크립트를 생성합니다.

**명명 규칙**: `{category}_{feature}.py` (예: `vid_extract_audio.py`)

```python
# src/scripts/my_new_tool.py
import sys
from pathlib import Path

def main(file_path: str):
    # 기능 구현
    print(f"Processing: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
```

#### 2. 설정 파일 추가
`config/menu_categories/` 내 해당 카테고리 JSON 파일에 항목을 추가합니다.

```json
{
    "category": "Tools",
    "id": "my_new_tool",
    "name": "My New Tool",
    "icon": "assets/icons/icon_my_tool.ico",
    "types": "*",
    "scope": "file",
    "enabled": true,
    "submenu": "ContextUp",
    "order": 1200,
    "gui": true,
    "dependencies": []
}
```

#### 3. 아이콘 추가 (선택)
`assets/icons/`에 아이콘을 추가합니다.
*   권장 크기: 24x24 또는 32x32
*   포맷: `.ico` 또는 `.png`

#### 4. 메뉴 새로고침
Manager에서 **"⟳ Refresh Menu"**를 클릭하여 변경사항을 반영합니다.
(별도의 빌드 과정 없이 자동으로 카테고리 파일을 로드합니다.)

---

### Python 환경 정책

> **모든 스크립트는 `tools/python/`의 Embedded Python에서 실행됩니다.**

*   시스템 Python에 의존하지 마세요.
*   라이브러리 설치 시: `tools/python/python.exe -m pip install <package>`
*   Conda 환경은 AI 워크로드(Torch, CUDA 등)에만 선택적으로 사용됩니다.

---

### 레지스트리 동작

`src/core/registry.py`의 `RegistryManager` 클래스가 Windows 레지스트리를 관리합니다.

*   **등록 위치**: `HKCU\Software\Classes\*\shell\ContextUp\...`
*   **마커**: 모든 등록 항목에 `ContextUpManaged=true` 값이 설정됩니다.
*   **동적 서브메뉴**: `dynamic_submenu` 속성으로 동적 메뉴(예: Copy My Info)를 등록합니다.

---

## 📄 라이선스

이 프로젝트는 [MIT License](LICENSE) 하에 배포됩니다.

---

**Made with ❤️ by ContextUp Contributors**
