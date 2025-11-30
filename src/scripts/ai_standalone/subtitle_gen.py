"""
Subtitle Generation using Faster-Whisper.
"""
import sys
import argparse
import time
from pathlib import Path
from faster_whisper import WhisperModel

def format_timestamp(seconds):
    """Format seconds to SRT timestamp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

def generate_subtitles(video_path, model_size="small", device="cuda", compute_type="float16", task="transcribe", language=None):
    """Generate subtitles for video."""
    try:
        print(f"Loading model {model_size} on {device}...")
        # Fallback to int8 if float16 is not supported on CPU or if CUDA fails
        if device == "cpu":
            compute_type = "int8"
            
        try:
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            print(f"Error loading model on {device}: {e}")
            if device == "cuda":
                print("Falling back to CPU...")
                device = "cpu"
                compute_type = "int8"
                model = WhisperModel(model_size, device=device, compute_type=compute_type)
            else:
                raise e
        
        print(f"Processing {video_path}...")
        segments, info = model.transcribe(video_path, beam_size=5, task=task, language=language)
        
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        suffix = f".{info.language}.srt"
        if task == "translate":
            suffix = ".en.srt"
            
        srt_path = Path(video_path).with_suffix(suffix)
            
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, start=1):
                start = format_timestamp(segment.start)
                end = format_timestamp(segment.end)
                text = segment.text.strip()
                
                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")
                
                # Print progress (flush to ensure realtime output in GUI)
                print(f"[{start} --> {end}] {text}", flush=True)
                
        print(f"\nSubtitles saved to: {srt_path}")
        return True
        
    except Exception as e:
        print(f"Error generating subtitles: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Subtitle Generation Tool')
    parser.add_argument('video_path', help='Input video path')
    parser.add_argument('--model', default='small', choices=['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'], help='Model size')
    parser.add_argument('--device', default='cuda', choices=['cuda', 'cpu'], help='Device to use')
    parser.add_argument('--task', default='transcribe', choices=['transcribe', 'translate'], help='Task (transcribe or translate to English)')
    parser.add_argument('--lang', help='Source language (optional)')
    
    args = parser.parse_args()
    
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"Error: File not found: {video_path}")
        return 1
        
    success = generate_subtitles(
        str(video_path),
        model_size=args.model,
        device=args.device,
        task=args.task,
        language=args.lang
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
