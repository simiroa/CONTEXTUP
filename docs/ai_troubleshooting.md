# HuggingFace 인증 및 가상환경 문제 해결 가이드

## 문제 1: HuggingFace 인증

RMBG-2.0과 BiRefNet은 gated repository로 HuggingFace 계정 인증이 필요합니다.

### 해결 방법

#### Step 1: HuggingFace 계정 생성
1. https://huggingface.co/join 방문
2. 무료 계정 생성

#### Step 2: Access Token 생성
1. https://huggingface.co/settings/tokens 방문
2. "New token" 클릭
3. Token 이름 입력 (예: "creator_tools")
4. Type: "Read" 선택
5. "Generate token" 클릭
6. **Token 복사** (한 번만 표시됨!)

#### Step 3: 모델 접근 권한 요청
1. https://huggingface.co/briaai/RMBG-2.0 방문
2. "Agree and access repository" 클릭
3. https://huggingface.co/ZhengPeng7/BiRefNet 방문
4. "Agree and access repository" 클릭

#### Step 4: Token 설정
```bash
# Conda 환경에서 실행
C:\Users\HG\miniconda3\envs\ai_tools\Scripts\pip.exe install huggingface-hub

# Token 로그인
C:\Users\HG\miniconda3\envs\ai_tools\python.exe -c "from huggingface_hub import login; login('YOUR_TOKEN_HERE')"
```

**또는 환경변수로 설정**:
```bash
# PowerShell에서
$env:HF_TOKEN = "YOUR_TOKEN_HERE"
```

---

## 문제 2: 가상환경 활성화 오류

에러 메시지: "Conda environment not set up"

### 원인
`ai_runner.py`가 `env_info.txt`를 찾지 못함

### 해결 방법 1: 자동 수정 (권장)

아래 스크립트 실행:
```bash
python tools/fix_ai_env.py
```

### 해결 방법 2: 수동 확인

1. 파일 존재 확인:
```bash
Test-Path "C:\Users\HG\Documents\HG_context_v2\src\scripts\ai_standalone\env_info.txt"
```

2. 없으면 생성:
```bash
# 내용:
CONDA_ENV_PATH=C:\Users\HG\miniconda3\envs\ai_tools
PYTHON_EXE=C:\Users\HG\miniconda3\envs\ai_tools\python.exe
PIP_EXE=C:\Users\HG\miniconda3\envs\ai_tools\Scripts\pip.exe
```

---

## 빠른 테스트

### InSPyReNet (인증 불필요)
```bash
# 이미지 우클릭 → Remove Background (AI) → InSPyReNet
```

### RMBG-2.0 (인증 후)
```bash
# Token 설정 후
# 이미지 우클릭 → Remove Background (AI) → RMBG-2.0
```

---

## 문제 해결

### "401 Client Error" 발생 시
- Token이 올바른지 확인
- 모델 접근 권한 승인 확인
- Token 재생성 후 다시 시도

### "env_info.txt not found" 발생 시
- `tools/fix_ai_env.py` 실행
- 또는 수동으로 파일 생성

### 여전히 안 될 경우
- Conda 환경 재생성:
```bash
conda remove -n ai_tools --all -y
python tools/setup_ai_conda.py
```
