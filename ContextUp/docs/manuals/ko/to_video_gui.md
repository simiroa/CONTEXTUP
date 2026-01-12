# Sequence to Video GUI (시퀀스 → 비디오 GUI)

## 소개
연속된 이미지 시퀀스(PNG, JPG, EXR 등)를 하나의 고화질 비디오 파일로 인코딩합니다. GUI로 상세 설정이 가능합니다.

## 사용법

1. 이미지 시퀀스 폴더 또는 첫 번째 이미지 선택 후 우클릭
2. **Sequence → Create Video from Sequence** 선택
3. 인코딩 설정:
   - **프레임레이트**: 24fps, 30fps, 60fps
   - **코덱**: H.264, H.265, ProRes
   - **품질**: CRF 또는 비트레이트
   - **해상도**: 원본 유지 또는 변경
4. **Start** 버튼으로 인코딩

## 지원 시퀀스 패턴
- `image_0001.png` (4자리 패딩)
- `frame.001.jpg` (dot 구분)
- `shot_v02_001.exr` (복합)

## 출력 포맷
| 포맷 | 코덱 | 용도 |
|-----|-----|-----|
| MP4 | H.264/H.265 | 범용, 웹 |
| MOV | ProRes | 편집용 |
| WebM | VP9 | 웹 최적화 |

## 의존성
- FFmpeg (자동 설치)
