def clean_cpu_gpu_name(name: str) -> str:
    return name.strip().title() if name else ""


def extract_requirements(text: str) -> Dict[str, List[Dict[str, Any]]]:
    def find_ram(text: str):
        match = re.search(r"(?i)(memory|ram):\s*(\d+)\s*GB", text)
        return int(match.group(2)) if match else None

    def find_storage(text: str):
        match = re.search(r"(?i)storage:\s*(\d+)\s*GB", text)
        return int(match.group(1)) if match else None

    def find_cpu(text: str):
        match = re.search(r"(?i)(cpu|processor):\s*([^\n\r]*)", text)
        return clean_cpu_gpu_name(match.group(2)) if match else None

    def find_gpu(text: str):
        match = re.search(
            r"(?i)(gpu|graphics|graphics card|video card):\s*([^\n\r]*)", text
        )
        return clean_cpu_gpu_name(match.group(2)) if match else None

    def detect_type(text: str):
        lower = text.lower()
        has_min = "minimum" in lower
        has_rec = "recommended" in lower
        if has_min and has_rec:
            return "both"
        elif has_min:
            return "minimum"
        elif has_rec:
            return "recommended"
        return "unknown"

    section_type = detect_type(text)
    requirements = []

    if section_type in ("minimum", "recommended", "unknown"):
        ram = find_ram(text)
        storage = find_storage(text)
        cpu = find_cpu(text)
        gpu = find_gpu(text)

        requirements.append(
            {
                "type": section_type if section_type != "unknown" else "minimum",
                "cpu": cpu,
                "gpu": gpu,
                "ram": ram,
                "storage": storage,
                "notes": (
                    text.strip()[:1000] if not (cpu or gpu or ram or storage) else None
                ),
            }
        )

    elif section_type == "both":
        lower = text.lower()
        min_index = lower.find("minimum")
        rec_index = lower.find("recommended")

        if min_index < rec_index:
            min_text = text[min_index:rec_index]
            rec_text = text[rec_index:]
        else:
            rec_text = text[rec_index:min_index]
            min_text = text[min_index:]

        for block, req_type in [(min_text, "minimum"), (rec_text, "recommended")]:
            ram = find_ram(block)
            storage = find_storage(block)
            cpu = find_cpu(block)
            gpu = find_gpu(block)

            requirements.append(
                {
                    "type": req_type,
                    "cpu": cpu,
                    "gpu": gpu,
                    "ram": ram,
                    "storage": storage,
                    "notes": (
                        block.strip()[:1000]
                        if not (cpu or gpu or ram or storage)
                        else None
                    ),
                }
            )

    return {
        "requirements": requirements,
        "confidence": sum(
            [cpu is not None, gpu is not None, ram is not None, storage is not None]
        )
        / 4.0,
    }
