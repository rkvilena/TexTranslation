import time
import easyocr
import cv2
import numpy as np

class TextDetectionRecognition:
    def __init__(self, language: list[str]) -> None:
        self.reader     = easyocr.Reader(language)
        self.image      = None
        self.drawnimg   = None
        self.detrectime = 0.0
        self.readresult: tuple(list,str,float)

    def load_image_file(self, imagepath):
        self.image = cv2.imread(imagepath)
    
    def load_image_arr(self, imagearr):
        self.image = imagearr

    def scan(self):
        drstart = time.time()
        self.readresult = self.reader.readtext(
            self.image,
            paragraph=True,
            x_ths=0,
        )
        self.detrectime += time.time()-drstart

    def read(self):
        self.load_image_arr(self.image)
        self.scan()
        return self.get_result()
    
    def save_drawn_img(self):
        cv2.imwrite("detection_res3.jpg", self.drawnimg)

    def get_result(self):
        return self.readresult
        # # Non-multiprocessing code
        # # To be updated
        # copy = self.image.copy()
        # for (boxes, text, _) in self.readresult:
        #     trstart = time.time()
        #     listofpoints = np.array(boxes, dtype=int)
        #     translated = self.translator.translate(text=text)
        #     (x, y) = (boxes[0][0], (boxes[0][1]+boxes[3][1])/2)
        #     boxw = abs(boxes[0][0] - boxes[1][0]) / 100.0
        #     self.trtime += time.time() - trstart

        #     print(f'Translation: {translated}')

        #     # cv2.polylines(copy, [pts], isClosed=True, color=(0,255,0), thickness=2)
        #     cv2.fillPoly(copy, [listofpoints], color=(255,255,255))
        #     cv2.putText(
        #         copy, translated, 
        #         [int(x), int(y)], 
        #         cv2.FONT_HERSHEY_SIMPLEX, 
        #         boxw / 4, (0,0,0), 1
        #     )
        # self.drawnimg = copy

    def show_detrec_duration(self):
        print(f"Detection & Recognition time: {self.detrectime}")