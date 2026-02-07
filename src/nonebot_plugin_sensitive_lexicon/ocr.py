import os
import tempfile
from pathlib import Path

import httpx
from cnocr import CnOcr

ocr = CnOcr()


async def _download_to_temp(url: str) -> Path:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        Path(path).write_bytes(resp.content)
        return Path(path)


async def ocr_text(img) -> str | None:
    """
    OCR 文本识别
    :param img: 本地路径或 URL
    :return:
    """
    temp_path: Path | None = None
    try:
        if isinstance(img, str) and img.startswith(("http://", "https://")):
            temp_path = await _download_to_temp(img)
            target = str(temp_path)
        else:
            target = img

        result = ocr.ocr(target)
        if result:
            return "\n".join(line.get("text", "") for line in result)
        return None
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)
