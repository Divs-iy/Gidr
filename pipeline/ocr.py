# from paddleocr import PaddleOCR
# import cv2
# import numpy as np
# import fitz
# class OCRProcessor:
#     def __init__(self):
#         print("🔄 Loading OCR model — this runs ONCE only")
#         self.ocr = PaddleOCR(
#             use_angle_cls=False,
#             lang='en',
#             use_gpu=False,
#             enable_mkldnn=True,   # ✅ CPU acceleration on Intel/Apple chips
#             cpu_threads=2,        # ✅ Caps CPU usage — stops fan noise
#             det_db_score_mode='fast',  # ✅ Faster text detection
#             rec_batch_num=6,      # ✅ Process 6 text regions at once instead of 1
#         )

#     def _pdf_to_images(self, pdf_path: str):
#         """Convert PDF pages to images for OCR."""
#         doc = fitz.open(pdf_path)
#         images = []
#         for page in doc:
#             # ✅ Render at 150 DPI — fast but readable (was default 72 which is too low)
#             mat = fitz.Matrix(150/72, 150/72)
#             pix = page.get_pixmap(matrix=mat)
#             img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
#                 pix.height, pix.width, pix.n
#             )
#             # PaddleOCR expects BGR, fitz gives RGB
#             if pix.n == 3:
#                 img_array = cv2.cvtColor(img_array.copy(), cv2.COLOR_RGB2BGR)
#             elif pix.n == 4:
#                 img_array = cv2.cvtColor(img_array.copy(), cv2.COLOR_RGBA2BGR)
            
#             images.append(img_array)
#         doc.close()
#         return images

#     def run_ocr(self, image_path):
#         is_pdf = image_path.lower().endswith('.pdf')

#         if is_pdf:
#             images = self._pdf_to_images(image_path)
#         else:
#             img = cv2.imread(image_path)
#             if img is None:
#                 raise ValueError(f"Image not found or invalid path: {image_path}")
#             images = [img]

#         extracted_data = []
        
#         for image in images:
#             # ✅ Resize large images
#             h, w = image.shape[:2]
#             if max(h, w) > 1500:
#                 scale = 1500 / max(h, w)
#                 image = cv2.resize(image, (int(w * scale), int(h * scale)))

#             results = self.ocr.predict(image)
#             for res in results:
#                 texts = res.get("rec_texts", [])
#                 scores = res.get("rec_scores", [])
#                 boxes = res.get("rec_boxes", [])
#                 for i in range(len(texts)):
#                     if scores[i] > 0.6:
#                         extracted_data.append({
#                             "text": texts[i],
#                             "confidence": scores[i],
#                             "bbox": boxes[i] if i < len(boxes) else None
#                         })

#         return {
#             "raw_text": " ".join([t['text'] for t in extracted_data]),
#             "words": extracted_data
#         }
import base64
import fitz  # PyMuPDF
import numpy as np
import cv2

class OCRProcessor:
    def __init__(self):
        print("✅ OCR Processor ready (vision mode — no local model)")

    def _image_to_base64(self, image: np.ndarray) -> str:
        """Convert numpy image array to base64 PNG string."""
        _, buffer = cv2.imencode('.png', image)
        return base64.b64encode(buffer).decode('utf-8')

    def _pdf_to_images(self, pdf_path: str):
        """Convert PDF pages to numpy images."""
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            mat = fitz.Matrix(150/72, 150/72)
            pix = page.get_pixmap(matrix=mat)
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            if pix.n == 3:
                img_array = cv2.cvtColor(img_array.copy(), cv2.COLOR_RGB2BGR)
            elif pix.n == 4:
                img_array = cv2.cvtColor(img_array.copy(), cv2.COLOR_RGBA2BGR)
            images.append(img_array)
        doc.close()
        return images

    def run_ocr(self, image_path: str) -> dict:
        """
        Instead of running local OCR, convert file to base64 images
        and return them for the extractor to send directly to Groq vision.
        """
        is_pdf = image_path.lower().endswith('.pdf')

        if is_pdf:
            images = self._pdf_to_images(image_path)
        else:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Image not found or invalid: {image_path}")
            # Resize if too large
            h, w = img.shape[:2]
            if max(h, w) > 1500:
                scale = 1500 / max(h, w)
                img = cv2.resize(img, (int(w * scale), int(h * scale)))
            images = [img]

        # Return base64 images — extractor will send to Groq vision
        return {
            "raw_text": "",  # empty — vision model reads image directly
            "images_b64": [self._image_to_base64(img) for img in images],
            "page_count": len(images)
        }