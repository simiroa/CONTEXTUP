# Save Clipboard Image (클립보드 이미지 저장)

## 소개
클립보드에 복사된 이미지 데이터를 감지하여 즉시 PNG 파일로 저장합니다.

## 사용법

1. 스크린샷 캡처 또는 이미지 복사 (Ctrl+C)
2. 저장할 폴더에서 우클릭
3. **Clipboard → Save Clipboard Image** 선택
4. 이미지가 즉시 저장됨

## 또는
- 트레이 메뉴에서 **Save Clipboard Image** 클릭
- 저장 위치 선택

## 출력 파일
- `clipboard_YYYYMMDD_HHMMSS.png`
- 타임스탬프 자동 생성

## 활용 예시
- 스크린샷 빠르게 저장
- 웹에서 복사한 이미지 저장
- 문서 이미지 추출
- 채팅에서 받은 이미지 저장

## 지원 형식
- PNG (무손실, 투명 지원)

## 의존성
- Pillow
