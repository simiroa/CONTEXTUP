# Conda 설치 가이드

## Conda가 감지되지 않았습니다

Phase 4 AI 기능을 사용하려면 Conda 환경이 필요합니다.

---

## 빠른 설치: Miniconda (권장)

### 1. Miniconda 다운로드
**Windows 64-bit 최신 버전**:
https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe

### 2. 설치 옵션
- ✅ "Add Miniconda3 to PATH" 체크 (중요!)
- ✅ "Register Miniconda3 as default Python" 체크
- 설치 경로: 기본값 사용 권장

### 3. 설치 확인
설치 후 새 PowerShell을 열고:
```bash
conda --version
```

출력 예시: `conda 24.x.x`

---

## 설치 후 다음 단계

### 1. AI 환경 설정 실행
```bash
cd C:\Users\HG\Documents\HG_context_v2
python tools/setup_ai_conda.py
```

### 2. 예상 소요 시간
- Conda 설치: ~5분
- AI 환경 설정: ~10분
- 총: ~15분

### 3. 다운로드 크기
- Miniconda: ~100MB
- PyTorch + CUDA: ~2GB
- AI 모델 (첫 실행 시): ~2-5GB

---

## 대안: Anaconda (더 많은 패키지 포함)

Anaconda를 이미 사용 중이라면 그대로 사용 가능합니다.

**다운로드**: https://www.anaconda.com/download

**차이점**:
- Miniconda: 최소 설치 (~100MB)
- Anaconda: 전체 패키지 (~3GB)

---

## 설치 없이 테스트 (임시)

Conda 없이 시스템 Python으로 테스트하려면:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install transformers pillow
```

**주의**: 시스템 Python 사용 시 의존성 충돌 가능성 있음

---

## 준비 완료 후

1. Conda 설치 완료
2. `python tools/setup_ai_conda.py` 실행
3. 이미지 파일 우클릭 → "Remove Background (AI)"
4. 3가지 모델 중 선택:
   - RMBG-2.0 (균형)
   - BiRefNet (최고 품질)
   - InSPyReNet (최고 속도)

---

## 문제 해결

### Conda 명령어가 인식되지 않음
- PowerShell을 재시작
- 시스템 재부팅
- PATH 환경변수 확인

### 설치 경로 찾기
기본 설치 경로:
- `C:\Users\[사용자명]\miniconda3`
- `C:\ProgramData\Miniconda3`

Conda 설치를 진행하시겠습니까?
