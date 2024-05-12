import time
import easyocr
import cv2

class TextDetectionRecognition:
    def __init__(self, language: list[str], use_gpu=True) -> None:
        self.reader     = easyocr.Reader(language, gpu=use_gpu)
        self.image      = None
        self.drawnimg   = None
        self.readresult: tuple[list[list[int,int]],str,float]
        self.detrectime = 0.0

    def load_image_file(self, imagepath):
        self.image = cv2.imread(imagepath)
    
    def load_image_arr(self, imagearr):
        self.image = imagearr
    
    def lang_change(self, lang: str):
        langlist = ['en']
        if lang != 'en': langlist = [lang, 'en']
        self.reader = easyocr.Reader(lang_list=langlist, change_lang=True)
        print("Change language completed!")

    def read(self, wths = 0.7, pmode = False, yths = 0.5):
        self.detrectime = time.time()
        self.grayscale_image()
        self.readresult = self.reader.readtext(
            self.image,
            width_ths=wths,
            paragraph=pmode,
            y_ths=yths,
        )
        return self.get_result()

    def grayscale_image(self):
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
    
    def save_drawn_img(self):
        cv2.imwrite("detection_res3.jpg", self.drawnimg)

    def get_result(self):
        boxes = [item[0] for item in self.readresult]
        texts = [item[1] for item in self.readresult]
        self.detrectime = time.time()-self.detrectime
        return [boxes, texts]

    def show_detrec_duration(self):
        print(f"Detection & Recognition time: {self.detrectime}")