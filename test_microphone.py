import sounddevice as sd
from scipy.io.wavfile import write

SAMPLE_RATE = 16000
DURATION = 5
DEVICE = 1

print("Speak in Telugu or English for 5 seconds...")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
    device=DEVICE,
)

sd.wait()

write("microphone_test.wav", SAMPLE_RATE, audio)

print("Recording saved as microphone_test.wav")