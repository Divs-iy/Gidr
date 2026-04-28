from paddleocr import PaddleOCR
import cv2

class OCRProcessor:
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

    def run_ocr(self, image_path):
        image = cv2.imread(image_path)
        

        if image is None:
            raise ValueError("Image not found or invalid path")

        results = self.ocr.predict(image)

        extracted_data = []

        # results is a list of dicts
        for res in results:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])
            boxes = res.get("rec_boxes", [])

            for i in range(len(texts)):
                extracted_data.append({
                    "text": texts[i],
                    "confidence": scores[i],
                    "bbox": boxes[i] if i < len(boxes) else None
                })

        return extracted_data