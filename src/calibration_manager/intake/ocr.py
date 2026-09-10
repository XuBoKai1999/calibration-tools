from pathlib import Path


def parse_image(image_path: Path) -> dict:
    from rapidocr import RapidOCR

    result = RapidOCR()(str(image_path))
    if not result.txts:
        raise ValueError("照片中沒有辨識到文字")
    return {
        "raw_text": "\n".join(result.txts),
        "mean_confidence": round(sum(result.scores) / len(result.scores), 4),
        "tokens": [
            {"text": text, "box": [[float(x), float(y)] for x, y in box], "confidence": float(score)}
            for text, box, score in zip(result.txts, result.boxes, result.scores)
        ],
    }
