# Changelog

All notable changes to ContextUp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [3.0.0] - 2024-12-12

### 🎉 Major Release

완전히 새로운 Manager UI와 성능 최적화, 새로운 기능들이 추가되었습니다.

### Added
- **Copy UNC Path**: 네트워크 경로를 UNC 형식으로 복사
- **DDS 입력 지원**: Image Converter에서 DDS 파일 읽기 지원
- **Quick Menu (Ctrl+Shift+C)**: 어디서든 빠르게 접근 가능한 팝업 메뉴
- **Settings 탭 재설계**: Tray Agent 통합, Quick Menu 인라인 표시
- **Widget Pooling**: Editor 프레임 위젯 재사용으로 렌더링 성능 향상

### Changed
- **Tray Poll Interval**: 5초 → 10초로 변경하여 CPU 사용량 감소
- **Resize Debounce**: 메인 창 크기 조정 시 150ms 딜레이 적용
- **Scroll Freeze**: 에디터 리스트 갱신 시 깜빡임 방지
- **아이콘 재생성**: 59개 아이콘 전체 재생성 (Soft Metal C4D 스타일)

### Removed
- **MoviePy 의존성**: FFmpeg로 충분히 처리되어 제거
- **불필요한 디버그 로그**: 오래된 로그 파일 정리

### Fixed
- Quick Menu와 Tray Menu 항목 동기화
- "Reopen Last Closed Folder" Quick Menu에서 동작하지 않던 문제
- "Open Folder from Clipboard" agent=None 에러 수정

---

## [2.x.x] - Previous Versions

이전 버전 기록은 Git 히스토리를 참조해 주세요.

---

## Categories

- **Added**: 새로운 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 관련
