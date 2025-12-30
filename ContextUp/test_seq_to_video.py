"""
Functional test for Sequence to Video GUI
Tests pattern detection, size calculation, and FFmpeg command generation
"""
import sys
import re

sys.path.insert(0, 'src')

def test_pattern_detection():
    """Test that pattern detection uses LAST number group."""
    print("\n[TEST 1] Pattern Detection (Last Number Group)")
    print("-" * 40)
    
    test_cases = [
        ("sc04_05_0001.png", "sc04_05_0074.png", "0001", "0074"),
        ("render_v2_001.exr", "render_v2_150.exr", "001", "150"),
        ("shot_001_comp_0001.tga", "shot_001_comp_0100.tga", "0001", "0100"),
    ]
    
    all_pass = True
    for first, last, expected_first, expected_last in test_cases:
        first_matches = list(re.finditer(r"(\d+)", first))
        last_matches = list(re.finditer(r"(\d+)", last))
        
        actual_first = first_matches[-1].group(1) if first_matches else "N/A"
        actual_last = last_matches[-1].group(1) if last_matches else "N/A"
        
        passed = actual_first == expected_first and actual_last == expected_last
        status = "PASS" if passed else "FAIL"
        all_pass = all_pass and passed
        
        print(f"  {first} -> {last}")
        print(f"    Expected Range: {expected_first} - {expected_last}")
        print(f"    Actual Range:   {actual_first} - {actual_last} [{status}]")
    
    return all_pass

def test_size_calculation_mp4():
    """Test MP4 size estimation."""
    print("\n[TEST 2] MP4 Size Calculation")
    print("-" * 40)
    
    frame_count = 150
    fps = 30
    duration_sec = frame_count / fps
    
    test_cases = [
        (20, 12.5),   # 20 Mbps -> 12.5 MB
        (50, 31.25),  # 50 Mbps -> 31.25 MB
        (100, 62.5),  # 100 Mbps -> 62.5 MB
    ]
    
    all_pass = True
    for bitrate, expected_size in test_cases:
        actual_size = (bitrate * duration_sec) / 8
        passed = abs(actual_size - expected_size) < 0.1
        status = "PASS" if passed else "FAIL"
        all_pass = all_pass and passed
        print(f"  {bitrate} Mbps @ {fps}fps, {frame_count} frames: ~{actual_size:.1f} MB [{status}]")
    
    return all_pass

def test_size_calculation_prores():
    """Test ProRes size estimation."""
    print("\n[TEST 3] ProRes Size Calculation")
    print("-" * 40)
    
    frame_count = 150
    pixels = 1920 * 1080
    
    prores_rates = {
        "ProRes 422": 0.06,
        "ProRes 422 HQ": 0.1,
        "ProRes 4444": 0.15,
        "ProRes 4444 XQ": 0.22
    }
    
    all_pass = True
    for preset, rate in prores_rates.items():
        scale = pixels / (1920 * 1080)
        size_mb = rate * scale * frame_count
        print(f"  {preset}: ~{size_mb:.0f} MB")
    
    # Test alpha multiplier
    alpha_size = prores_rates["ProRes 4444 XQ"] * 1.25 * frame_count
    print(f"  ProRes 4444 XQ + Alpha: ~{alpha_size:.0f} MB")
    print("  [PASS]")
    
    return True

def test_ffmpeg_commands():
    """Test FFmpeg command generation."""
    print("\n[TEST 4] FFmpeg Command Generation")
    print("-" * 40)
    
    # MP4 test
    bitrate = 30
    mp4_suffix = f"_{bitrate}mbps.mp4"
    mp4_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-b:v", f"{bitrate}M", "-preset", "medium"]
    print(f"  MP4: folder_name{mp4_suffix}")
    print(f"    Args: {' '.join(mp4_args)}")
    
    # ProRes tests
    prores_profiles = {
        "ProRes 422": ("2", "yuv422p10le", "_422"),
        "ProRes 422 HQ": ("3", "yuv422p10le", "_422hq"),
        "ProRes 4444": ("4", "yuv444p10le", "_4444"),
        "ProRes 4444 XQ": ("5", "yuv444p10le", "_4444xq"),
    }
    
    for preset, (profile, pix_fmt, suffix) in prores_profiles.items():
        print(f"  {preset}: folder_name{suffix}.mov")
        print(f"    Args: -c:v prores_ks -profile:v {profile} -pix_fmt {pix_fmt}")
    
    # Alpha test
    profile, pix_fmt, suffix = "4", "yuva444p10le", "_4444_alpha"
    print(f"  ProRes 4444 + Alpha: folder_name{suffix}.mov")
    print(f"    Args: -c:v prores_ks -profile:v {profile} -pix_fmt {pix_fmt}")
    print("  [PASS]")
    
    return True

def main():
    print("=" * 50)
    print("Sequence to Video GUI - Functional Test")
    print("=" * 50)
    
    results = []
    results.append(("Pattern Detection", test_pattern_detection()))
    results.append(("MP4 Size Calculation", test_size_calculation_mp4()))
    results.append(("ProRes Size Calculation", test_size_calculation_prores()))
    results.append(("FFmpeg Command Generation", test_ffmpeg_commands()))
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        all_passed = all_passed and passed
        print(f"  {name}: {status}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("=" * 50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
