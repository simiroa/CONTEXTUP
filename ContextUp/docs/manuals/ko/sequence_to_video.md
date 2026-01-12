# Sequence to Video (시퀀스 → 비디오)

## 소개
이미지 시퀀스(연번 이미지)를 비디오 파일로 인코딩합니다.

## 지원 입력
- **PNG 시퀀스**: image_0001.png, image_0002.png...
- **EXR 시퀀스**: frame_0001.exr, frame_0002.exr...
- **JPG 시퀀스**: shot_001.jpg, shot_002.jpg...
- **TIFF 시퀀스**: render_0001.tif...

## 사용법

1. 시퀀스 폴더 또는 첫 번째 이미지 선택 후 우클릭
2. **Sequence → Sequence to Video** 선택
3. 옵션 설정:
   - **프레임레이트**: 24fps, 30fps, 60fps
   - **출력 코덱**: H.264, H.265, ProRes
   - **품질**: CRF 또는 비트레이트
4. 인코딩 시작

## 출력 포맷
- MP4 (H.264/H.265)
- MOV (ProRes)
- WebM (VP9)

## 활용 예시
- 3D 렌더 시퀀스를 비디오로
- 타임랩스 사진을 영상으로
- 애니메이션 프레임 합성

## 의존성
- FFmpeg (자동 설치)
