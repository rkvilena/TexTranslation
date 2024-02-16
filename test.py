import cv2
import numpy as np
import pygetwindow as gw
from PIL import ImageGrab

class ScreenOperator:
    def capture(self, x, y, w, h):
        ss = np.ndarray(ImageGrab.grab(bbox=(x,y,w,h)))
        

    