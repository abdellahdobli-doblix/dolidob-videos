"""Free, local text-to-speech with Kokoro (Apache-2.0 open model), used when ElevenLabs is not.

Usage: python scripts/tts_kokoro.py jobs.json
jobs.json: [{"text": "...", "voice": "af_heart", "out": "tmp/line0.wav"}, ...]
Loads the model once and writes one 24 kHz WAV per job.
"""
import json
import sys

import numpy as np
import soundfile as sf
from kokoro import KPipeline

jobs = json.load(open(sys.argv[1]))
pipe = KPipeline(lang_code="a")  # American English
for job in jobs:
    chunks = [audio for _, _, audio in pipe(job["text"], voice=job["voice"], speed=job.get("speed", 1.0))]
    audio = np.concatenate([np.asarray(c) for c in chunks]) if chunks else np.zeros(2400)
    sf.write(job["out"], audio, 24000)
    print(f"{job['out']}: {len(audio) / 24000:.2f} s ({job['voice']})")
