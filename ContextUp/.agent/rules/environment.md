---
trigger: always_on
---

프로젝트 컨벤션 (conventions.md)

## 코딩 컨벤션
- GUI 파일은 `_gui.py` 접미사 사용
- 모든 사용자 메시지는 한국어로
- customtkinter 사용 시 다크 테마 기본
- config 파일은 JSON 형식
3. 테스트 관련 (testing.md)

## 테스트 시 주의
- GUI 테스트 시 `mainloop()` 호출 전 스크린샷 캡처
- 터미널에서 GUI 실행 중이면 정상 동작으로 간주
- `WINDOW_FAIL`은 윈도우가 안 보이는 것, 에러 아님

4. 자주 하는 실수 방지 (common_mistakes.md)

## 피해야 할 실수
- `sys.path` 수정 시 `parent.parent`로 src 폴더 참조
- relative import 대신 absolute import 사용
- JSON 파일 수정 후 trailing comma 확인
- 내장 /tools/python 파이썬 경로를 가장 먼저 확인할 것