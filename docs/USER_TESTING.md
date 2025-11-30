# 사용자 테스트 및 기능 현황

이 문서는 **Creator Tools v2**의 모든 기능에 대한 현황, 아키텍처 리스크, 그리고 사용자 피드백을 추적합니다. 검증을 위한 체크리스트로 활용하세요.

## 1. 시스템 유틸리티 (Sys)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Folder: Move to New...** | 선택한 파일을 새 폴더로 이동합니다. | **Batch Runner**: `batch_runner.py`를 사용하여 여러 프로세스를 조율합니다. <br>⚠️ **리스크**: 네트워크 드라이브에서 잠금 파일(Lock file) 권한 오류 가능성. | ✅ 완료 |
| **Folder: Remove Empty** | 빈 하위 디렉토리를 재귀적으로 삭제합니다. | **Recursive Walk**: 표준 `os.walk` 사용. <br>⚠️ **리스크**: 숨겨진 시스템 파일만 있는 폴더를 빈 폴더로 오인하여 삭제할 수 있음 (로직상 체크는 함). | ✅ 완료 |
| **Folder: Find Missing Frames** | 이미지 시퀀스에서 누락된 프레임 번호를 찾습니다. | **Regex**: 파일명에서 숫자를 추출하여 연속성을 검사합니다. <br>⚠️ **리스크**: 파일명에 숫자가 여러 개일 경우(예: `shot01_v02.001.png`) 엉뚱한 숫자를 인식할 수 있음. | ✅ 완료 |
| **Folder: Arrange Sequences** | 접두사(prefix)를 기준으로 파일을 폴더별로 정리합니다. | **Regex**: 특정 명명 패턴(`name.001.ext`)에 의존합니다. <br>⚠️ **리스크**: 복잡한 파일명에서 오탐지 가능성. | ✅ 완료 |
| **Clipboard: Save Image** | 클립보드의 이미지를 파일로 저장합니다. | **Pillow**: `ImageGrab.grabclipboard()` 사용. <br>⚠️ **리스크**: 클립보드에 이미지가 없거나 호환되지 않는 형식이면 실패. | ✅ 완료 |
| **Clipboard: Analyze Image** | 클립보드 이미지를 Ollama(Vision)로 분석합니다. | **Ollama**: 로컬 LLM 추론. <br>⚠️ **리스크**: Ollama 서버가 실행 중이어야 함. VRAM 부족 시 실패. | ✅ 완료 |
| **Clipboard: Analyze Error** | 클립보드의 에러 메시지를 분석하여 해결책을 제안합니다. | **LLM**: 텍스트 기반 LLM 추론. <br>⚠️ **리스크**: 인터넷 연결 필요 (Gemini/GPT 사용 시) 또는 로컬 LLM 성능 의존. | ✅ 완료 |
| **Open Creator Tools Manager** | 설정 및 레지스트리 관리 GUI를 엽니다. | **Registry Access**: `HKCU\Software\Classes`를 수정합니다. <br>⚠️ **리스크**: 백신 프로그램이 레지스트리 쓰기를 차단할 수 있음. | ✅ 완료 |

## 2. 이름 변경 (Rename)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Batch Rename...** | 통합 이름 변경 GUI (접두사/접미사/삭제). | **Tkinter**: 표준 GUI 사용. <br>⚠️ **리스크**: 파일 목록이 매우 많을 경우(1만 개 이상) 미리보기가 느려지거나 멈출 수 있음. | ✅ 완료 |
| **Renumber...** | 파일 시퀀스 번호 재설정. | **Sorting**: 파일 정렬 후 이름 변경. <br>⚠️ **리스크**: 원본 파일명과 대상 파일명이 겹칠 때(Collision) 데이터 손실 주의 (임시 이름 사용으로 방지함). | ✅ 완료 |

## 3. 이미지 도구 (Image)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Convert Image Format** | 이미지 일괄 변환 (JPG, PNG, WEBP 등). | **Pillow**: 대부분 Pillow 사용. <br>⚠️ **리스크**: 투명도가 있는 이미지를 JPG로 변환 시 배경색 처리(검은색/흰색) 주의. | ✅ 완료 |
| **Remove EXIF Data** | 이미지 메타데이터(EXIF) 제거. | **Pillow**: 데이터를 복사하여 새 이미지 생성. <br>⚠️ **리스크**: 일부 비표준 메타데이터는 남을 수 있음. | ✅ 완료 |
| **Resize to Power of 2** | 게임 텍스처용 POT 리사이즈 (512, 1024...). | **Pillow**: Lanczos 리샘플링. <br>⚠️ **리스크**: "Stretch" 모드는 비율을 왜곡하므로 UI/텍스처 용도로만 사용해야 함. | ✅ 완료 |
| **Split EXR Layers** | EXR 파일의 레이어를 개별 파일로 분리. | **FFmpeg**: `ffmpeg.exe` 사용. <br>⚠️ **리스크**: 채널 이름이 복잡한 경우 매핑이 올바르지 않을 수 있음. | ✅ 완료 |
| **Merge to EXR** | 여러 이미지를 하나의 레이어드 EXR로 병합. | **FFmpeg**: `ffmpeg.exe` 사용. <br>⚠️ **리스크**: 입력 이미지들의 해상도가 다르면 실패함. | ✅ 완료 |
| **AI Upscale (2x/4x)** | 4배 업스케일링 (Real-ESRGAN). | **Dual Env**: `ai_tools` Conda 환경 호출. <br>⚠️ **리스크**: CPU에서는 매우 느림. CUDA 필수. | ✅ 완료 |
| **Remove Background (AI)** | AI 배경 제거 (RMBG-2.0). | **Dual Env**: `ai_tools` Conda 환경 호출. <br>⚠️ **리스크**: VRAM 사용량 높음. Conda 환경 의존성. | ✅ 완료 |
| **Analyze Image (Ollama)** | 이미지를 텍스트로 설명/분석. | **Ollama**: 로컬 Vision 모델 사용. <br>⚠️ **리스크**: 모델 로딩 시간 소요. | ✅ 완료 |
| **Auto Tag Metadata (AI)** | AI로 태그 생성 후 메타데이터에 삽입. | **Dual Env**: 태깅 모델 사용. <br>⚠️ **리스크**: 기존 메타데이터를 덮어쓸 수 있음. | ✅ 완료 |
| **Texture Tools (Gemini/PBR)** | PBR 맵 생성 (Normal, Roughness). | **Gemini API**: 클라우드 API 사용. <br>⚠️ **리스크**: API 키 필요. 일일 사용량 제한. | ✅ 완료 |

## 4. 비디오 도구 (Video)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Convert Video / Proxy** | 비디오 변환 및 프록시 생성. | **FFmpeg**: `ffmpeg.exe` 의존. <br>⚠️ **리스크**: 코덱 호환성 문제 (특히 ProRes/DNxHD). | ✅ 완료 |
| **Sequence to Video** | 이미지 시퀀스를 비디오로 변환. | **FFmpeg**: 패턴 매칭. <br>⚠️ **리스크**: 시퀀스 중간에 빈 번호(Gap)가 있으면 실패. | ✅ 완료 |
| **Frame Interpolation (AI)** | AI 프레임 보간 (RIFE). | **Dual Env**: RIFE 모델 사용. <br>⚠️ **리스크**: 매우 무거운 작업. VRAM 부족 시 충돌 가능. | ✅ 완료 |
| **Frame Interpolation (to 30fps)** | 단순 프레임 블렌딩/중복. | **FFmpeg**: 필터 사용. <br>⚠️ **리스크**: 품질이 AI보다 낮음 (고스트 현상). | ✅ 완료 |
| **Audio Tools** | 오디오 추출/제거/분리. | **FFmpeg/Demucs**: 분리는 AI 사용. <br>⚠️ **리스크**: Demucs 모델 다운로드 필요. | ✅ 완료 |
| **Generate Subtitles** | 음성 -> 자막 (.srt). | **Faster-Whisper**: 로컬 모델. <br>⚠️ **리스크**: 긴 영상은 시간이 오래 걸림. | ✅ 완료 |

## 5. 오디오 도구 (Audio)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Convert Audio Format** | 오디오 포맷 변환. | **FFmpeg**: `ffmpeg.exe` 사용. <br>⚠️ **리스크**: 메타데이터 손실 가능성. | ✅ 완료 |
| **Optimize Volume** | 음량 평준화 (Loudnorm). | **FFmpeg**: EBU R128 알고리즘. <br>⚠️ **리스크**: 두 번 인코딩(2-pass)하므로 시간이 걸림. | ✅ 완료 |

## 6. 3D 도구 (3D)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Convert CAD to OBJ** | STEP/IGES -> OBJ 변환. | **Mayo**: `mayo_console.exe` 사용. <br>⚠️ **리스크**: 테셀레이션 품질 조절 불가. | ✅ 완료 |
| **Convert Mesh Format** | 3D 메쉬 변환 (FBX/OBJ/GLTF). | **Blender**: `blender.exe` 사용. <br>⚠️ **리스크**: Blender 버전 호환성 (3.0+ 권장). | ✅ 완료 |
| **Extract Textures** | 3D 파일에서 텍스처 추출. | **Blender**: 텍스처 언팩 기능 사용. <br>⚠️ **리스크**: 임베딩되지 않은 텍스처는 추출 불가. | ✅ 완료 |

## 7. 문서 도구 (Document)

| 기능 | 역할 | 아키텍처 및 리스크 | 상태 |
| :--- | :--- | :--- | :--- |
| **Merge PDFs** | PDF 병합. | **pypdf**: 순수 Python. <br>⚠️ **리스크**: 암호화된 PDF 실패. | ✅ 완료 |
| **Split PDF** | PDF 분할. | **pypdf**: 순수 Python. <br>⚠️ **리스크**: 대용량 PDF 처리 시 메모리 사용량. | ✅ 완료 |
| **Analyze Document** | PDF 내용 분석/요약. | **Ollama**: 로컬 LLM. <br>⚠️ **리스크**: 텍스트 추출이 불가능한 스캔된 PDF는 인식 불가 (OCR 미지원). | ✅ 완료 |

---

## 📝 피드백 로그 (Feedback Log)

*   **2024-11-28**: "새 폴더로 이동" 시 여러 창이 뜨는 문제 해결 (`batch_runner.py` 구현).
*   **2024-11-28**: `BatchProgressGUI` 추가로 "중지(Stop)" 버튼 반응성 및 진행바 표시 문제 해결.
*   **2024-11-28**: Manager GUI에서 기능 이름을 변경하여 정렬 순서를 제어할 수 있도록 개선.
*   **2024-11-28**: 문서 누락 기능(클립보드, EXR, 오디오 도구 등) 전체 업데이트 완료.
