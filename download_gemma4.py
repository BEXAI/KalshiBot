import os
from transformers import AutoProcessor, AutoModelForImageTextToText

print("Starting native Transformers download sequence for google/gemma-4-31B...")

config = "google/gemma-4-31B"

print(f"Downloading PreProcessor for {config}...")
processor = AutoProcessor.from_pretrained(config)

print(f"Downloading AutoModelForImageTextToText for {config}...")
model = AutoModelForImageTextToText.from_pretrained(config)

print("Download successfully complete and cached into Hugging Face ~/.cache/huggingface!")
