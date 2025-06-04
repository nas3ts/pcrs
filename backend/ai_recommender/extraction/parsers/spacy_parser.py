import spacy
import re
from typing import Dict, List, Any

nlp = spacy.load("en_core_web_sm")


def clean_cpu_gpu_name(name: str) -> str:
    return name.strip().title() if name else ""


def extract_spacy_requirements(text: str) -> Dict[str, List[Dict[str, Any]]]:
    doc = nlp(text.lower())

    def extract_value(pattern: str) -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    cpu = extract_value(r"(?:cpu|processor)\s*:\s*([^\n\r]+)")
    gpu = extract_value(r"(?:gpu|graphics|graphics card|video card)\s*:\s*([^\n\r]+)")
    ram = extract_value(r"(?:ram|memory)\s*:\s*(\d+)\s*gb")
    storage = extract_value(r"(?:storage)\s*:\s*(\d+)\s*gb")

    confidence = (
        sum([cpu is not None, gpu is not None, ram is not None, storage is not None])
        / 4.0
    )

    return {
        "requirements": [
            {
                "type": "minimum",  # default; you can improve this with heuristics
                "cpu": clean_cpu_gpu_name(cpu),
                "gpu": clean_cpu_gpu_name(gpu),
                "ram": int(ram) if ram else None,
                "storage": int(storage) if storage else None,
                "notes": text[:1000],
                "confidence": confidence,
            }
        ]
    }
