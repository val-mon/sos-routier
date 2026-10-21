# src: https://huggingface.co/OpenMOSS-Team/MOSS-Transcribe-Diarize#quickstart

import os
from pathlib import Path

import librosa
import torch
from pydub import AudioSegment
from transformers import AutoModelForCausalLM, AutoProcessor

model_id = "OpenMOSS-Team/MOSS-Transcribe-Diarize"

# load processor and model
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    device_map="auto",
    torch_dtype="auto",
).eval()


def convert_to_wav(audio_dir: str):
    for file in os.scandir(audio_dir):
        path_file = Path(file.path)
        if path_file.suffix.lower() != ".wav":
            AudioSegment.from_file(path_file).export(
                path_file.with_suffix(".wav"), format="wav"
            )
            os.remove(file)


def transcribe_audio(audio_path: str) -> str:
    wav_path = Path(audio_path)

    # load audio file
    target_sr = getattr(
        getattr(processor, "feature_extractor", None), "sampling_rate", 16000
    )
    audio_array, sampling_rate = librosa.load(wav_path, sr=target_sr)

    # prompt creation
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "audio", "audio": wav_path},
            ],
        }
    ]
    prompt_text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # input preparation
    inputs = processor(
        text=prompt_text,
        audio=audio_array,
        sampling_rate=sampling_rate,
        return_tensors="pt",
    ).to(model.device)

    for k, v in inputs.items():
        if torch.is_floating_point(v):
            inputs[k] = v.to(model.dtype)

    # generation of the transcription
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=False,
        )

    # cut input tokens and decode the output
    input_len = inputs["input_ids"].shape[1]
    transcription = processor.decode(
        generated_ids[0, input_len:], skip_special_tokens=True
    )

    return transcription


if __name__ == "__main__":
    convert_to_wav("res")

    print("\n", "-" * 20, "TRANSCRIPTION", "-" * 20)
    audio_dir = Path("res")
    for file in os.scandir(audio_dir):
        print(transcribe_audio(file.path))
