# ContextUp

<p align="center">
  <img src="assets/icons/ContextUp.ico" width="80" alt="ContextUp Logo">
</p>

<p align="center">
  <b>Windows 우클릭 메뉴를 통한 통합 생산성 플랫폼</b><br>
  파일 관리 • 미디어 편집 • 로컬 AI
</p>

---

## ✨ 주요 기능

| 카테고리 | 대표 기능 | 설명 |
|---------|----------|-----|
| 📁 **System** | [Finder](docs/manuals/ko/finder.md), [Batch Rename](docs/manuals/ko/batch_rename.md) | 파일 탐색, 중복 검사, 일괄 이름 변경 |
| 🖼️ **Image** | [Convert](docs/manuals/ko/image_convert.md), [Vectorizer](docs/manuals/ko/rigreader_vectorizer.md) | 이미지 형식 변환, SVG 벡터화 |
| 🎬 **Video** | [Convert](docs/manuals/ko/video_convert.md), [Extract Audio](docs/manuals/ko/extract_audio.md) | 비디오 변환, 오디오 추출 |
| 🎵 **Audio** | [Convert](docs/manuals/ko/audio_convert.md), [Demucs](docs/manuals/ko/demucs_stems.md) | 오디오 변환, AI 음원 분리 |
| 📄 **Document** | [PDF Merge](docs/manuals/ko/pdf_merge.md), [Doc Convert](docs/manuals/ko/doc_convert.md) | PDF 병합/분할, 문서 변환 |
| 🤖 **AI** | [Upscale](docs/manuals/ko/esrgan_upscale.md), [Whisper](docs/manuals/ko/whisper_subtitle.md) | AI 업스케일, 자막 생성 |
| 🎨 **3D** | [Mesh Convert](docs/manuals/ko/mesh_convert.md), [Auto LOD](docs/manuals/ko/auto_lod.md) | 3D 메쉬 변환, LOD 생성 |
| 📊 **Tools** | [Monitor Widget](docs/manuals/ko/monitor_widget.md), [AI Text Lab](docs/manuals/ko/ai_text_lab.md) | 시스템 모니터, AI 텍스트 처리 |

## 📖 문서

- [**상세 기능 가이드**](docs/user/FEATURES.md) - 전체 기능 목록 및 상세 설명
- [**매뉴얼 폴더**](docs/manuals/ko/) - 각 기능별 상세 사용법

## 🚀 설치

### 요구사항
- Windows 10/11
- Python 3.11 (자동 설치)
- NVIDIA GPU (AI 기능용, 선택)

### 설치 방법
```powershell
# 1. 저장소 클론
git clone https://github.com/simiroa/CONTEXTUP.git
cd CONTEXTUP

# 2. 설치 실행
python src/setup/install.py
```

### 설치 티어
| 티어 | 용량 | 주요 기능 |
|-----|-----|---------|
| 🟢 **Minimal** | ~500MB | 기본 유틸리티 |
| 🟡 **Standard** | ~2GB | 미디어 편집 + API AI |
| 🔴 **Full** | ~10GB | 로컬 AI (GPU 필요) |

## 🎯 빠른 시작

1. **설치 후** 트레이 아이콘 확인
2. **파일 우클릭** → ContextUp 메뉴 사용
3. **단축키**: `Ctrl+Shift+C` (퀵 메뉴)
4. **관리**: 트레이 아이콘 더블클릭 (Manager)

## ⚙️ 설정

Manager에서 설정 가능한 항목:
- API 키 (Gemini, Ollama)
- 외부 도구 경로 (Blender, ComfyUI)
- 메뉴 항목 표시/숨김
- 단축키 설정

## 📝 라이선스

MIT License

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/simiroa">simiroa</a>
</p>
