import cv2

class Preprocessor:
    def preprocess(self, image_path):
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError("Image not found")
        # light upscale only (important for OCR clarity)
        image = cv2.resize(image, None, fx=1.5, fy=1.5)

        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # blur = cv2.GaussianBlur(gray, (3, 3), 0)

        # thresh = cv2.adaptiveThreshold(
        #     blur,
        #     255,
        #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #     cv2.THRESH_BINARY,
        #     11,
        #     2
        # )

        # 🔴 FIX: convert back to 3 channels
        #processed = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        return image

# class Preprocessor:
#     def preprocess(self, image_path):
#         image = cv2.imread(image_path)

#         if image is None:
#             raise ValueError("Image not found")

#         # light upscale only (important for OCR clarity)
#         image = cv2.resize(image, None, fx=1.5, fy=1.5)

#         return image