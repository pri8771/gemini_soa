import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from typing import List
def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[Image.Image]:
    return convert_from_path(pdf_path, dpi=dpi)
def ocr_images(images: list) -> str:
    return "\n".join([pytesseract.image_to_string(img) for img in images])
