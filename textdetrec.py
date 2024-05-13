import time
import easyocr
import cv2
import winocr
import json
from memory_profiler import profile

class EasyOCRdetrec:
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
        finalboxes = []
        for i in range(len(boxes)):
            h = int(boxes[i][2][1]-boxes[i][0][1])
            w = int(boxes[i][2][0]-boxes[i][0][0])
            x = int(boxes[i][0][0])
            y = int(boxes[i][0][1])
            finalboxes.append((h,w,x,y))
        texts = [item[1] for item in self.readresult]
        self.detrectime = time.time()-self.detrectime
        return [finalboxes, texts]

    def show_detrec_duration(self):
        print(f"Detection & Recognition time: {self.detrectime}")

class WinOCRdetrec:
    def __init__(self, language: str) -> None:
        self.lang       = language
        self.image      = None
        self.drawnimg   = None
        self.readresult: list[list[tuple[int,int,int,int], str]]
        self.detrectime = 0.0

    def load_image_file(self, imagepath):
        self.image = cv2.imread(imagepath)
    
    def load_image_arr(self, imagearr):
        self.image = imagearr
    
    def lang_change(self, lang: str):
        self.lang = lang

    def read(self):
        self.detrectime = time.time()
        res = json.loads(json.dumps(winocr.recognize_cv2_sync(self.image, self.lang)))
        self.readresult = [self.get_bbox_result(res),self.get_text_result(res)]
        self.detrectime = time.time()-self.detrectime
        return self.readresult

    def grayscale_image(self):
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def get_text_result(self, detrec_res):
        textlist = []
        for texts in detrec_res["lines"]:
            textlist.append(texts["text"])
        return textlist

    def get_bbox_result(self, detrec_res):
        position_list = []
        for textlist in detrec_res["lines"]:
            h = 0
            w = 0
            x = int(textlist["words"][0:1][0]['bounding_rect']['x'])
            y = int(textlist["words"][0:1][0]['bounding_rect']['y'])
            for words in textlist["words"]:
                h = max(h, words['bounding_rect']['height'])
                w += words['bounding_rect']['width']
            position_list.append((int(h*1.4), int(w*1.1), x, y))
        return position_list

    def show_detrec_duration(self):
        print(f"Detection & Recognition time: {self.detrectime}")