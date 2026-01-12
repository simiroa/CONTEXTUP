import os
from pathlib import Path

manuals = {
    # Video
    "video_convert": {
        "name": "Video Convert",
        "category": "Video",
        "intro": "비디오 파일의 포맷을 고화질로 변환합니다. (MP4, MOV, AVI, MKV, WEBM 지원)",
        "usage": [
            "변환할 비디오 파일을 선택하고 우클릭합니다.",
            "**Video -> Video Convert**를 클릭하여 변환 창을 엽니다.",
            "대상 포맷과 비트레이트 설정을 확인한 후 **Convert**를 누릅니다."
        ]
    },
    "extract_audio": {
        "name": "Extract Audio",
        "category": "Video",
        "intro": "비디오에서 오디오 트랙만 추출하여 고품질 MP3 또는 WAV 파일로 저장합니다.",
        "usage": [
            "비디오 파일을 우클릭하고 **Video -> Extract Audio**를 선택합니다.",
            "자동으로 오디오 추출이 시작되며, 결과물은 원본과 같은 폴더에 저장됩니다."
        ]
    },
    "interpolate_30fps": {
        "name": "Interpolate 30fps",
        "category": "Video",
        "intro": "AI가 아닌 FFmpeg 보간 필터를 사용하여 비디오를 30fps로 부드럽게 변환합니다.",
        "usage": [
            "원본 비디오를 우클릭하고 **Video -> Interpolate 30fps**를 선택합니다.",
            "진행 상태바가 100%가 될 때까지 기다리면 보간된 영상이 생성됩니다."
        ]
    },
    "create_proxy": {
        "name": "Create Proxy",
        "category": "Video",
        "intro": "영상 편집 시 성능을 높이기 위해 저해상도/저용량의 프록시 파일을 생성합니다.",
        "usage": [
            "편집할 고화질 영상을 우클릭하고 **Video -> Create Proxy**를 선택합니다.",
            "편집 툴에서 해당 프록시 파일을 연결하여 가볍게 편집할 수 있습니다."
        ]
    },
    "remove_audio": {
        "name": "Remove Audio",
        "category": "Video",
        "intro": "비디오에서 소리를 완전히 제거하여 무음 영상(Mute)으로 만듭니다.",
        "usage": [
            "파일 우클릭 후 **Video -> Remove Audio**를 선택하면 즉시 소리가 제거된 복사본이 생성됩니다."
        ]
    },
    
    # AI
    "whisper_subtitle": {
        "name": "Whisper Subtitle AI",
        "category": "AI",
        "intro": "OpenAI의 Whisper 인공지능을 사용하여 영상의 음성을 텍스트로 받아쓰고 자막 파일을 생성합니다.",
        "usage": [
            "영상 파일을 우클릭하고 **AI -> Whisper Subtitle AI**를 선택합니다.",
            "사용할 언어(한국어, 영어 등)와 모델 크기를 설정합니다.",
            "**Generate** 버튼을 누르면 영상과 동일한 이름의 .srt 파일이 생성됩니다."
        ]
    },
    "esrgan_upscale": {
        "name": "ESRGAN Upscale",
        "category": "AI",
        "intro": "Real-ESRGAN 알고리즘을 사용하여 저해상도 이미지의 품질을 잃지 않으면서 해상도를 4배로 높입니다.",
        "usage": [
            "이미지 파일을 우클릭하고 **AI -> ESRGAN Upscale**을 선택합니다.",
            "업스케일링이 완료되면 원본 파일명 뒤에 _upscaled가 붙은 파일이 생성됩니다."
        ]
    },
    "rmbg_background": {
        "name": "RMBG Background Removal",
        "category": "AI",
        "intro": "최신 배경 제거 AI를 사용하여 복잡한 배경에서도 피사체만 깔끔하게 따냅니다.",
        "usage": [
            "인물이나 사물이 포함된 이미지를 우클릭하고 **AI -> RMBG Background Removal**을 선택합니다.",
            "배경이 투명하게 처리된 PNG 파일이 즉시 생성됩니다."
        ]
    },
    "marigold_pbr": {
        "name": "Marigold PBR Generator",
        "category": "AI",
        "intro": "일반 사진 한 장으로부터 뎁스(Depth)와 노멀(Normal) 정보를 추출하여 3D 소스로 활용 가능한 맵을 생성합니다.",
        "usage": [
            "텍스처나 사진을 우클릭하고 **AI -> Marigold PBR Generator**를 선택합니다.",
            "생성할 맵 종류를 선택하고 실행하면 고품질의 텍스처 맵들이 생성됩니다."
        ]
    },
    "gemini_image_tool": {
        "name": "Gemini Image Tool",
        "category": "AI",
        "intro": "Google Gemini Vision API를 연동하여 이미지의 내용을 분석하거나 태그를 생성합니다.",
        "usage": [
            "이미지를 우클릭하고 **AI -> Gemini Image Tool**을 선택합니다.",
            "분석 프롬프트를 입력하거나 기본 분석을 실행하여 텍스트 결과를 얻을 수 있습니다."
        ]
    },
    "demucs_stems": {
        "name": "Demucs Stem Separation",
        "category": "AI",
        "intro": "Demucs AI 모델을 사용하여 음악 파일에서 보컬, 베이스, 드럼, 기타 소리를 각각 별도의 파일로 분리합니다.",
        "usage": [
            "음악 파일을 우클릭하고 **AI -> Demucs Stem Separation**을 선택합니다.",
            "분리된 결과물은 각 파트별 이름이 붙은 여러 개의 파일로 저장됩니다."
        ]
    },
    
    # Image
    "image_convert": {
        "name": "Image Convert",
        "category": "Image",
        "intro": "범용 이미지 포맷뿐만 아니라 전문적인 RAW, PSD, EXR 포맷들을 일괄 변환합니다.",
        "usage": [
            "하나 이상의 이미지를 선택하고 우클릭합니다.",
            "**Image -> Image Convert**에서 대상 포맷(WebP, PNG 등)을 선택한 후 실행합니다."
        ]
    },
    "merge_to_exr": {
        "name": "Merge to EXR",
        "category": "Image",
        "intro": "여러 장의 이미지를 하나의 멀티레이어 EXR 파일로 묶어 관리합니다. (합성 작업 시 유용)",
        "usage": [
            "합칠 이미지들을 모두 선택하고 우클릭합니다.",
            "**Image -> Merge to EXR**을 선택하여 레이어 이름을 정의하고 저장합니다."
        ]
    },
    "resize_power_of_2": {
        "name": "Resize Power of 2",
        "category": "Image",
        "intro": "이미지를 256, 512, 1024 등 2의 거듭제곱 크기로 리사이즈합니다. 게임 엔진 최적화에 필수입니다.",
        "usage": [
            "원본 이미지를 우클릭하고 **Image -> Resize Power of 2**를 선택합니다.",
            "가장 가까운 2의 거듭제곱 혹은 지정된 크기로 리사이즈됩니다."
        ]
    },
    "split_exr": {
        "name": "Split EXR",
        "category": "Image",
        "intro": "멀티레이어로 구성된 EXR 파일을 개별 이미지 파일들로 다시 분리합니다.",
        "usage": [
            "EXR 파일을 우클릭하고 **Image -> Split EXR**을 선택합니다."
        ]
    },
    "texture_packer_orm": {
        "name": "Texture Packer ORM",
        "category": "Image",
        "intro": "R(Occlusion), G(Roughness), B(Metallic) 맵을 하나의 ORM 텍스처 채널로 병합합니다.",
        "usage": [
            "각 채널에 들어갈 3장의 이미지를 선택하거나 한 장을 우클릭하여 실행합니다.",
            "각 채널에 맞는 파일을 드래그하여 할당한 후 저장합니다."
        ]
    },
    "normal_flip_green": {
        "name": "Normal Flip Green",
        "category": "Image",
        "intro": "노멀 맵의 그린 채널을 반전시킵니다. (Y+ -> Y- 변환)",
        "usage": [
            "노멀 맵 파일을 우클릭하고 **Image -> Normal Flip Green**을 선택합니다."
        ]
    },
    "rigreader_vectorizer": {
        "name": "RigReady Vectorizer",
        "category": "Image",
        "intro": "일반 이미지를 무한 확장이 가능한 벡터(SVG) 형식으로 정밀하게 변환합니다. 일러스트레이터용 작업을 돕습니다.",
        "usage": [
            "변환할 이미지를 우클릭하고 **Image -> RigReady Vectorizer** 프로젝트를 엽니다.",
            "배경 제거 유무와 디테일 수준을 조절하여 벡터화합니다."
        ]
    },
    
    # System
    "clean_empty_folders": {
        "name": "Clean Empty Folders",
        "category": "System",
        "intro": "불필요하게 남아있는 빈 폴더들을 모두 찾아 한꺼번에 제거하여 프로젝트 구조를 깨끗하게 만듭니다.",
        "usage": [
            "대상 폴더를 우클릭하고 **System -> Clean Empty Folders**를 선택합니다."
        ]
    },
    "move_to_new_folder": {
        "name": "Move to New Folder",
        "category": "System",
        "intro": "여러 파일을 선택하여 한 번에 새 폴더를 만들고 그 안으로 이동시키는 기능을 제공합니다.",
        "usage": [
            "파일들을 선택하고 우클릭한 뒤 **System -> Move to New Folder**를 누릅니다.",
            "생성할 폴더 이름을 입력하면 즉시 이동됩니다."
        ]
    },
    "unwrap_folder": {
        "name": "Unwrap Folder",
        "category": "System",
        "intro": "폴더 안에 내용물만 꺼내오고 싶을 때 사용합니다. 폴더 구조를 해제합니다.",
        "usage": [
            "해당 폴더를 우클릭하고 **System -> Unwrap Folder**를 선택합니다."
        ]
    },
    "finder": {
        "name": "Dup Finder",
        "category": "System",
        "intro": "이름이 다르더라도 내용이 완전히 같은 중복 파일을 찾아내어 용량을 확보합니다.",
        "usage": [
            "탐색할 경로를 선택하고 **System -> Dup Finder**를 실행합니다."
        ]
    },
    "batch_rename": {
        "name": "Batch Rename",
        "category": "System",
        "intro": "수백 개의 파일 이름을 일정한 규칙(넘버링, 날짜, 문자열 치환 등)으로 빠르게 변경합니다.",
        "usage": [
            "파일들을 선택하고 우클릭한 뒤 **System -> Batch Rename**을 선택합니다.",
            "규칙을 설정하고 미리보기를 통해 확인 후 시스템에 적용합니다."
        ]
    },
    
    # 3D
    "auto_lod": {
        "name": "Auto LOD",
        "category": "3D",
        "intro": "고해상도 메쉬의 폴리곤 개수를 줄여 실시간 렌더링에 적합한 LOD 모델을 자동 생성합니다.",
        "usage": [
            "3D 파일을 우클릭하고 **3D -> Auto LOD**를 선택합니다.",
            "원하는 감소 비율을 입력하고 최적화된 메쉬를 내보냅니다."
        ]
    },
    "mesh_convert": {
        "name": "Mesh Convert",
        "category": "3D",
        "intro": "FBX, OBJ, GLB, USD 등 다양한 3D 프로젝트 간 파일 포맷을 상호 변환합니다.",
        "usage": [
            "3D 모델을 우클릭하고 **3D -> Mesh Convert**를 클릭합니다.",
            "목표 포맷을 선택하여 변환된 새로운 메쉬 파일을 얻습니다."
        ]
    },
    "extract_textures": {
        "name": "Extract Textures",
        "category": "3D",
        "intro": "FBX 파일 내부에 포함(Embed)된 텍스처들을 외부 이미지 파일로 분리하여 추출합니다.",
        "usage": [
            "FBX 파일을 우클릭하고 **3D -> Extract Textures**를 선택합니다."
        ]
    },
    
    # Document
    "pdf_merge": {
        "name": "PDF Merge",
        "category": "Document",
        "intro": "여러 개의 PDF 문서를 하나의 연속된 PDF 문서로 합칩니다.",
        "usage": [
            "합치고자 하는 PDF 파일들을 모두 선택하고 우클릭합니다.",
            "**Document -> PDF Merge**를 선택하여 순서를 확인하고 저장합니다."
        ]
    },
    "pdf_split": {
        "name": "PDF Split",
        "category": "Document",
        "intro": "다중 페이지 PDF 문서를 각 페이지별 개별 파일로 분리합니다.",
        "usage": [
            "PDF 파일을 우클릭하고 **Document -> PDF Split**를 선택합니다."
        ]
    },
    "to_video_gui": {
        "name": "Sequence to Video",
        "category": "Sequence",
        "intro": "연속된 이미지 시퀀스(PNG, JPG 등)를 하나의 고화질 비디오 파일로 렌더링합니다.",
        "usage": [
            "이미지 시퀀스가 들어있는 폴더를 우클릭하거나 시퀀스 파일을 선택합니다.",
            "**Sequence -> Create Video from Sequence**를 선택합니다.",
            "프레임 레이트(FPS)와 코덱 설정을 마친 후 인코딩을 시작합니다."
        ]
    },
    "arrange_sequences": {
        "name": "Arrange Sequences",
        "category": "Sequence",
        "intro": "난잡하게 흩어진 이미지 시퀀스들을 프레임 번호에 따라 폴더별로 깔끔하게 정리해줍니다.",
        "usage": [
            "정리할 파일들이 있는 폴더를 우클릭하고 **Sequence -> Arrange Sequences**를 선택합니다."
        ]
    },
    
    # ComfyUI
    "seedvr2_upscaler": {
        "name": "SeedVR2 Video Upscaler",
        "category": "ComfyUI",
        "intro": "ComfyUI의 SeedVR2 워크플로우를 사용하여 비디오의 품질을 극대화하고 AI 업스케일링을 수행합니다.",
        "usage": [
            "비디오 파일을 우클릭하고 **ComfyUI -> SeedVR2 Video Upscaler**를 선택합니다.",
            "ComfyUI 서버가 실행 중이어야 하며, 자동으로 워크플로우를 전송하여 작업을 시작합니다."
        ]
    },
    "creative_studio_z": {
        "name": "ComfyUI Creative Studio (Z)",
        "category": "ComfyUI",
        "intro": "아이콘 생성, 에셋 제작 등에 최적화된 Z-Turbo 워크플로우 기반의 통합 워크스페이스입니다.",
        "usage": [
            "바탕화면 우클릭 또는 매니저를 통해 **Creative Studio (Z)**를 실행합니다.",
            "프롬프트 레이어와 AI 엔진을 조합하여 실시간으로 에셋을 생성할 수 있습니다."
        ]
    },
    "creative_studio_advanced": {
        "name": "ComfyUI Creative Studio (Advanced)",
        "category": "ComfyUI",
        "intro": "LoRA 스태킹, FaceDetailer, SUPIR 등 고급 기능을 포함한 프로페셔널 AI 이미지 생성 도구입니다.",
        "usage": [
            "**ComfyUI -> Creative Studio (Advanced)**를 실행합니다.",
            "고급 모델 설정을 통해 세밀한 이미지 컨트롤이 가능합니다."
        ]
    },
    "ace_audio_editor": {
        "name": "Creative Audio Studio (ACE)",
        "category": "ComfyUI",
        "intro": "AI를 활용한 오디오 생성 및 편집 기능을 제공하는 통합 오디오 스튜디오입니다.",
        "usage": [
            "오디오 파일을 우클릭하거나 직접 실행하여 **Creative Audio Studio (ACE)**를 엽니다."
        ]
    },
    "comfyui_dashboard": {
        "name": "Open Web UI",
        "category": "ComfyUI",
        "intro": "설치된 ComfyUI의 웹 대시보드를 직접 엽니다. 서버가 꺼져 있다면 자동으로 실행합니다.",
        "usage": [
            "**ComfyUI -> Open Web UI**를 선택합니다."
        ]
    },
    
    # Other Tools
    "audio_convert": {
        "name": "Audio Convert",
        "category": "Audio",
        "intro": "오디오 파일의 포맷을 변환합니다 (MP3, WAV, FLAC, OGG, M4A 지원).",
        "usage": [
            "오디오 파일을 우클릭하고 **Audio -> Audio Convert**를 선택합니다.",
            "목표 포맷을 선택하고 실행합니다."
        ]
    },
    "extract_bgm": {
        "name": "Extract BGM",
        "category": "Audio",
        "intro": "오디오 파일에서 목소리를 제거하고 배경음악(BGM)만 남깁니다.",
        "usage": [
            "오디오 또는 영상 파일을 우클릭하고 **Audio -> Extract BGM**을 선택합니다."
        ]
    },
    "extract_voice": {
        "name": "Extract Voice",
        "category": "Audio",
        "intro": "오디오 파일에서 배경음을 제거하고 목소리(Voice)만 선명하게 추출합니다.",
        "usage": [
            "오디오 또는 영상 파일을 우클릭하고 **Audio -> Extract Voice**를 선택합니다."
        ]
    },
    "normalize_volume": {
        "name": "Normalize Volume",
        "category": "Audio",
        "intro": "여러 오디오 파일의 볼륨을 일정한 수준으로 평준화하여 소리 크기를 맞춥니다.",
        "usage": [
            "오디오 파일을 우클릭하고 **Audio -> Normalize Volume**을 선택합니다."
        ]
    },
    
    # Utilities
    "copy_my_info": {
        "name": "Copy My Info",
        "category": "Tools",
        "intro": "자주 사용하는 텍스트 정보(계좌번호, 주소 등)를 등록해두고 빠르게 복사할 수 있는 도구입니다.",
        "usage": [
            "트레이 아이콘 우클릭 메뉴 또는 **Tools -> Copy My Info**에서 등록된 정보를 클릭하여 복사합니다."
        ]
    },
    "youtube_downloader": {
        "name": "Video Downloader",
        "category": "Tools",
        "intro": "YouTube 등 다양한 웹사이트의 영상을 URL만으로 간단히 다운로드합니다.",
        "usage": [
            "프로그램을 실행하고 영상 주소(URL)를 입력합니다.",
            "해상도를 선택한 뒤 다운로드 버튼을 누릅니다."
        ]
    },
    "leave_manager": {
        "name": "Leave Manager",
        "category": "Tools",
        "intro": "휴가일수를 관리하고 다음 휴가까지 남은 시간을 카운트다운합니다.",
        "usage": [
            "트레이 메뉴에서 **Leave Manager**를 실행하여 휴가 계획을 관리하세요."
        ]
    },
    "prompt_master": {
        "name": "Prompt Master",
        "category": "Tools",
        "intro": "AI에게 전달할 프롬프트를 체계적으로 관리하고, 최적의 프롬프트로 다듬어주는 도구입니다.",
        "usage": [
            "트레이 메뉴에서 **Prompt Master**를 실행합니다."
        ]
    },
    "monitor_widget": {
        "name": "Monitor Widget",
        "category": "Tools",
        "intro": "CPU, GPU(NVIDIA), 메모리 등 시스템 자원 사용량을 실시간으로 감시하는 위젯입니다.",
        "usage": [
            "트레이 메뉴에서 **Monitor Widget**을 켜면 바탕화면에 실시간 그래프가 표시됩니다.",
            "위젯을 드래그하여 원하는 위치에 놓을 수 있습니다."
        ]
    },
    "ai_text_lab": {
        "name": "AI Text Lab",
        "category": "AI",
        "intro": "다양한 AI 모델을 활용하여 텍스트 요약, 번역, 코드 분석 등을 수행하는 실험실입니다.",
        "usage": [
            "텍스트 파일을 우클릭하거나 도구를 실행하여 텍스트를 입력합니다.",
            "원하는 프리셋(요약, 번역 등)을 선택하여 질의합니다."
        ]
    }
}

def generate():
    manuals_dir = Path("docs/manuals")
    template = """# {name}

## Introduction
{intro}

## Usage
{usage_list}
"""
    for item_id, info in manuals.items():
        usage_str = "\n".join([f"{i+1}. {step}" for i, step in enumerate(info['usage'])])
        content = template.format(
            name=info['name'],
            intro=info['intro'],
            usage_list=usage_str
        )
        
        target_path = manuals_dir / f"{item_id}.md"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated manual: {item_id}.md")

if __name__ == "__main__":
    generate()
