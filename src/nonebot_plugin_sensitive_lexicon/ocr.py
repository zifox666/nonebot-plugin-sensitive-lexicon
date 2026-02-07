import os
import tempfile
from pathlib import Path

import httpx
from paddleocr import PaddleOCR


class OCRImg:
    def __init__(self):
        self._client: httpx.AsyncClient = httpx.AsyncClient()
        self.ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_server_det",
            text_recognition_model_name="PP-OCRv5_server_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    async def get_image(self, url: str) -> Path:
        resp = await self._client.get(url)
        resp.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        Path(path).write_bytes(resp.content) #noqa: ASYNC240
        return Path(path)

    async def text(
        self, img, min_confidence: float = 0.8, join_with: str = "\n"
    ) -> str | None:
        """
        从 PaddleOCR 返回中提取文字，按 `min_confidence` 过滤并用 `join_with` 拼接。
        返回 None 表示没有满足置信度的文本。
        """
        temp_path: Path | None = None
        try:
            if isinstance(img, str) and img.startswith(("http://", "https://")):
                temp_path = await self.get_image(img)
                target = str(temp_path)
            else:
                target = img

            result = self.ocr.ocr(target)

            if not result or not result[0]:
                return None
            extracted_texts = []
            for line in result[0]:
                try:
                    text_content, confidence = line[1]
                except: #noqa: E722
                    continue
                if confidence >= min_confidence:
                    extracted_texts.append(text_content)

            if not extracted_texts:
                return None

            return join_with.join(extracted_texts)
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)


ocr = OCRImg()
