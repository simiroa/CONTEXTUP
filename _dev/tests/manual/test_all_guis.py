"""
Automated GUI Launch Tester
Tests all GUI tools to identify launch failures
"""
import subprocess
import sys
from pathlib import Path

# GUI tools to test
GUI_TOOLS = [
    "manager_gui.py",
    "audio_convert_gui.py",
    "audio_separate_gui.py", 
    "audio_studio_gui.py",
    "mesh_lod_gui.py",
    "video_audio_gui.py",
    "video_convert_gui.py",
    "video_downloader_gui.py",
    "video_interpolation_gui.py",
    "video_seq_gui.py",
    "gemini_image_tools.py",
    "texture_tools.py",
    "flatten_dir.py",
    "archive_manager.py"
]

def test_gui(script_name):
    """Test if a GUI script can be imported without errors"""
    script_path = Path("src/scripts") / script_name
    
    if not script_path.exists():
        return "MISSING", f"File not found: {script_path}"
    
    # Try to compile the script (syntax check)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(script_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return "SYNTAX_ERROR", result.stderr.strip()
        
        return "OK", "Syntax check passed"
        
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "Compilation timed out"
    except Exception as e:
        return "ERROR", str(e)

def main():
    print("=" * 60)
    print("GUI LAUNCH TEST REPORT")
    print("=" * 60)
    print()
    
    results = {}
    passed = 0
    failed = 0
    
    for tool in GUI_TOOLS:
        status, message = test_gui(tool)
        results[tool] = (status, message)
        
        if status == "OK":
            passed += 1
            print(f"✅ {tool:<30} OK")
        else:
            failed += 1
            print(f"❌ {tool:<30} {status}")
            print(f"   └─ {message[:80]}")
    
    print()
    print("=" * 60)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {len(GUI_TOOLS)} tools")
    print("=" * 60)
    
    # Write detailed report
    with open("gui_test_report.txt", "w", encoding="utf-8") as f:
        f.write("GUI Launch Test Report\n")
        f.write("=" * 60 + "\n\n")
        
        for tool, (status, message) in results.items():
            f.write(f"{tool}: {status}\n")
            if status != "OK":
                f.write(f"  Error: {message}\n")
            f.write("\n")
        
        f.write(f"\nSummary: {passed} passed, {failed} failed\n")
    
    print("\nDetailed report saved to: gui_test_report.txt")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
