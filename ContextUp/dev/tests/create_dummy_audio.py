import wave
import math
import struct

def create_dummy_audio(filename="test_audio.wav", duration=1.0):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(n_samples):
            value = int(32767.0 * math.sin(2 * math.pi * 440 * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframes(data)
            
    print(f"Created {filename}")

if __name__ == "__main__":
    create_dummy_audio()
