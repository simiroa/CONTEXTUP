# ContextUp 설치 가이드

> **아키텍처**: 로컬 Python 3.11 (Standalone) + 통합 라이브러리 + Userdata 분리
> **최신 업데이트**: 2025-12-23 (v4.0.1)

---

## 아키텍처 개요

ContextUp은 시스템 환경과 완전히 분리된 **독립형 Python 환경**과 **문서화된 데이터 구조**를 사용합니다.

| 항목 | 값 | 설명 |
|-----|-----|------|
| Python 버전 | 3.11 (IndyGreg Standalone) | 시스템 Python과 충돌 없음 |
| 설치 위치 | `ContextUp/tools/python/` | 앱 폴더 내에 자립적으로 존재 |
| 설정(App) | `ContextUp/config/` | 앱 기본 설정 (Git 관리) |
| 데이터(User)| `ContextUp/userdata/` | 개인 설정, API 키, 로컬 히스토리 (Git 제외) |

> [!IMPORTANT]
> **V4.0.0 업데이트**: 사용자 데이터 파일이 `config/`에서 `userdata/` 디렉토리로 이동되었습니다. 기존 사용자는 설치 시 자동으로 마이그레이션됩니다. (`config/runtime/*.json` 포함)

---

## 🚀 빠른 설치

### 1. 자동 설치 및 마이그레이션

```bash
install.bat
```

**수행되는 작업:**
1. 독립형 Python 3.11 다운로드 및 압축 해제 (`tools/python/`)
2. `src/setup/install.py`를 통한 의존성 패키지 설치 (티어별 선택)
3. **기존 데이터 마이그레이션**: `config/`와 `config/runtime/`에 있던 개인 설정을 `userdata/`로 이동
4. ContextUp Manager 자동 실행

> **TIP**: `install.bat`는 embedded Python이 있으면 이를 우선 사용하고, 없을 때만 시스템 Python으로 부트스트랩합니다.

---

## 🔧 외부 도구 및 라이브러리

### 외부 도구 (ContextUp/tools/)

일부 고성능 기능은 다음 도구들이 `ContextUp/tools/` 아래에 설치되어 있어야 활성화됩니다.

| 도구 | 폴더명 | 용도 |
|-----|------|-----|
| **FFmpeg** | `ffmpeg/` | 비디오/오디오 스트림 처리 |
| **Blender** | `blender/` | 3D 데이터 처리 및 베이크 |
| **ComfyUI** | `ComfyUI/` | AI 이미지/영상 고수준 처리 |
| **Mayo** | `Mayo/` | CAD 데이터 변환 |
| **Real-ESRGAN**| `realesrgan/` | 이미지 업스케일 바이너리 (또는 `resources/bin/`) |

### AI 라이브러리 (Python)

설치 시 GPU 환경(NVIDIA)에 맞춰 자동으로 최적화된 버전이 설치됩니다.

| 라이브러리 | AI 기능 |
|-----------|--------|
| **PyTorch** | AI 모델 실행 핵심 (ESRGAN, Marigold, RIFE 등) |
| **Rembg** | 배경 제거 |
| **Faster-Whisper**| 고속 자막 생성 |
| **Demucs** | 음원 분리 |

---

## 📂 디렉토리 구조 상세 (V4.0+)

```
ContextUp/
├─ src/             # 핵심 소스 코드
├─ config/          # 앱 기본 설정 및 카테고리 정의 (정적)
│  └─ categories/   # 각 메뉴 항목 설정 (Flattened)
├─ userdata/        # 사용자 데이터 (동적, 백업 필수)
│  ├─ settings.json # 앱 전역 설정
│  ├─ secrets.json # API 키 (Gemini 등)
│  ├─ user_overrides.json # 메뉴 커스텀 내역
│  ├─ gui_states.json # GUI 상태 저장
│  ├─ download_history.json # 다운로드 기록
│  └─ copy_my_info.json # 개인 정보 템플릿
├─ tools/           # 내장 Python 및 외부 실행 도구
└─ resources/        # AI 모델 및 고정 리소스
```

---

## Troubleshooting

문제 발생 시 [Troubleshooting Guide](../dev/TROUBLESHOOTING.md)를 참조하세요. 주요 점검 사항:
- `userdata/secrets.json`의 Gemini API 키 유효성 확인
- `tools/ffmpeg/ffmpeg.exe` 등 외부 도구 경로 확인
- GPU 가속이 작동하지 않을 경우 NVIDIA 드라이버 버전 확인

---

## 제거 (Uninstall)

```bash
# 레지스트리 해제 및 도구 정리
uninstall.bat
```
