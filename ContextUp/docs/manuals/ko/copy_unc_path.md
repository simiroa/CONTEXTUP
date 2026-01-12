# Copy UNC Path (UNC 경로 복사)

## 소개
네트워크 공유 폴더 호환 형식(`\\Server\Share\...`)으로 파일/폴더 경로를 복사합니다.

## 사용법

1. 파일 또는 폴더 선택 후 우클릭
2. **Clipboard → Copy UNC Path** 선택
3. UNC 형식 경로가 클립보드에 복사됨

## 예시
- **원본**: `Z:\Project\Assets\texture.psd`
- **UNC**: `\\FileServer\Projects\Project\Assets\texture.psd`

## 활용 예시
- 팀원에게 네트워크 경로 공유
- 매핑된 드라이브가 다른 PC에서도 열 수 있는 경로 전송
- 배치 스크립트에서 UNC 경로 사용

## 기능
- **자동 변환**: 드라이브 문자를 서버 경로로
- **즉시 복사**: 한 번의 클릭으로 완료
- **네트워크 검증**: 연결된 네트워크 드라이브 자동 감지

## 참고
- 로컬 드라이브(C:, D:)는 UNC 변환 불가
- 네트워크 드라이브만 변환 가능
