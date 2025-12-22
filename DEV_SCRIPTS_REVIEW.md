• 높음
                                                                                          
  - ContextUp/docs/user/README_KR.md에서 Manager 실행을 ContextUpManager.bat로 안내하지만 
    실제 파일은 manager.bat뿐입니다. 설치 직후 진입 단계가 바로 막힙니다.                 
  - ContextUp/docs/dev/AGENT_GUIDELINES.md와 ContextUp/docs/dev/TESTING_GUIDE.md가 config/    menu/categories와 config/menu_config.json 기준으로 안내하지만 실제 로더는 config/     
    categories만 읽습니다 (ContextUp/src/core/config.py, ContextUp/config/categories). 잘 
    못된 위치에 수정이 쌓일 위험이 큽니다.                                                
  - 외부 바이너리 경로를 ContextUp/resources/bin로 고정하라는 문서 지침이 있으나, 실제 설 
    치/탐색은 대부분 ContextUp/tools 기준입니다 (ContextUp/docs/dev/AGENT_GUIDELINES.md,  
    ContextUp/docs/dev/DEVELOPMENT.md, ContextUp/dev/scripts/setup_tools.py, ContextUp/   
    src/utils/external_tools.py). Real‑ESRGAN만 resources/bin 우선 조회라 FFmpeg/Blender/ 
    Mayo는 문서대로 두면 인식 실패 가능성이 있습니다.                                     
  - ContextUp/docs/user/FEATURES.md는 RT Translator를 NLLB 오프라인 + Ctrl+Alt+T로 안내하 
    지만, 실제 구현은 deep_translator 기반 GoogleTranslator(네트워크 필요)이고 hotkey도 정    의돼 있지 않습니다 (ContextUp/src/features/system/translator.py, ContextUp/config/    
    categories/tools.json, ContextUp/src/tray/agent.py).                                  
                                                                                          
  중간                                                                                    
                                                                                          
  - ContextUp/docs/user/FEATURES.md에서 YouTube Downloader/Finder를 트레이 접근으로 안내하    고 Finder에 Alt+Space를 붙여두었지만, 실제 show_in_tray가 false이고 Finder hotkey도 없    습니다 (ContextUp/config/categories/tools.json, ContextUp/config/categories/          
    system.json, ContextUp/src/tray/agent.py).                                            
  - ContextUp/docs/user/FEATURES.md에 interpolate_30fps(Video)와 reopen_recent(System)이  
    누락되어 현재 기능 목록이 불완전합니다 (ContextUp/config/categories/video.json,       
    ContextUp/config/categories/system.json).                                             
  - ComfyUI 기능 안내가 디스패처와 맞지 않습니다. ContextUp/docs/user/FEATURES.md는       
    SeedVR2/Z Image Turbo를 사용 가능하다고 하지만 ContextUp/src/core/menu.py에 해당 ID 핸    들러가 없어 실행되지 않습니다 (ContextUp/config/categories/comfyui.json). 또한        
    ContextUp/docs/dev/DEVELOPMENT.md의 script/show_in_context_menu 예시는 현재 디스패처/ 
    레지스트리에서 읽히지 않습니다 (ContextUp/src/core/menu.py, ContextUp/src/core/       
    registry.py).                                                                         
  - ContextUp/docs/user/INSTALL.md는 install.bat이 requirements.txt를 설치한다고 적지만 실    제 설치는 ContextUp/src/setup/install.py의 내부 패키지 목록을 사용합니다 (ContextUp/  
    requirements.txt).                                                                    
  - ContextUp/docs/dev/TROUBLESHOOTING.md에 crash_log.txt, src/manager/core/settings.py,  
    tray_agent.py, reprod_restart.py가 등장하나 현재 경로/파일이 아닙니다 (실제 로그는    
    ContextUp/logs/manager_crash.log, 트레이는 ContextUp/src/tray/agent.py, 설정은        
    ContextUp/src/core/settings.py). 또 ContextUp/docs/dev/TESTING_GUIDE.md에는           
    video_audio_tools ID가 있지만 config에 없습니다 (ContextUp/config/categories/         
    video.json).                                                                          
                                                                                          
  질문/가정                                                                               
                                                                                          
  - ComfyUI 항목(SeedVR2/Z Image Turbo)을 실제로 노출할 계획인지, 문서 정정 vs ContextUp/ 
    src/core/menu.py 핸들러 추가 중 어떤 방향이 맞나요?                                   
  - 외부 바이너리 공식 기준 경로를 ContextUp/tools로 고정할지, ContextUp/resources/bin까지    포함한 혼합 규칙으로 갈지 정책 확인이 필요합니다.                                     
  - RT Translator를 오프라인(NLLB)로 돌릴 계획인지, 현재 GoogleTranslator 방식으로 유지할 
    지 결정이 있나요?                                                                     
                                                                                          
  변경 요약                                                                               
                                                                                          
  - 변경 없음(문서-코드 정합성 분석만 수행).      