import subprocess
import os

def test_piper_tts():
    sample_text = "Hello, this is a test to verify Piper TTS setup."
    output_wav = "piper_test_output.wav"
    voice_model = r"C:\Users\gawan\OneDrive\Desktop\LdamProject\piper\voices\en_US-amy-low.onnx"
    piper_path = r"C:\Users\gawan\OneDrive\Desktop\LdamProject\piper\piper\piper.exe"

    command = [
        piper_path,
        "--model", voice_model,
        "--output", output_wav
    ]

    print("Running Piper TTS command...")
    result = subprocess.run(command, input=sample_text.encode(), capture_output=True)

    if result.returncode != 0:
        print("Piper TTS failed with error:\n", result.stderr.decode())
        return False

    if os.path.exists(output_wav):
        print(f"✅ Success! Audio file '{output_wav}' created.")
        print(f"File size: {os.path.getsize(output_wav)} bytes")
        return True
    else:
        print("❌ Failed: Audio file was not created.")
        return False

if __name__ == "__main__":
    success = test_piper_tts()
    print("Piper TTS is set up correctly." if success else "Piper TTS setup test failed.")
