# voici - voiceclone

Clone your own voice from a short recording, then speak any text with it. Runs locally, free.

## Setup (Python 3.10 - 3.12)

    python -m venv .venv
    # Windows:  .venv\Scripts\activate
    # macOS:    source .venv/bin/activate
    pip install -r requirements.txt

Optional but recommended: install ffmpeg so you can use mp3/m4a recordings.
- Windows: `winget install ffmpeg`
- macOS: `brew install ffmpeg`

Windows + NVIDIA GPU: install the CUDA build of PyTorch first for fast generation
(pick the command at https://pytorch.org/get-started/locally/), then run the pip install above.

## Use

    python voiceclone.py --ref my_voice.wav --text "Hello, this is my cloned voice." --out hello.wav
    python voiceclone.py --ref my_voice.wav --text "مرحبا، هذا صوتي" --out arabic.wav
    python voiceclone.py --ref my_voice.wav            # interactive mode

First run downloads the model (~2 GB) and asks you to accept the Coqui license (CPML, non-commercial).

## Getting a good clone

- 15-30 seconds of you talking naturally, in a quiet room, no music, no echo.
- Use the same mic and tone you want in the output (read it expressively if you want expressive results).
- Clone quality is best in the language you recorded; cross-language works but loses some accent fidelity.
