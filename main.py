import cv2
import time
from detection import EAST
from recognition import CRNN
import concurrent


east = EAST()
crnn = CRNN()

detect_map, boxes, ratio = east.exec("tests/mic.jpg")

word_list = []

def recognize_word(box, ori, ratio, crnn):
    a, b, c, d = box
    a = int(ratio[0]*a)
    b = int(ratio[1]*b)
    c = int(ratio[0]*c)
    d = int(ratio[1]*d)
    cropped = ori[b:d,a:c]
    word_list.append(crnn.exec(cropped))

for box in boxes:
    recognize_word(box, east.original, ratio, crnn)

cv2.imwrite("detection_res1.jpg", detect_map)

print(f"Detection duration = {east.duration}")
print(f"Recognition duration = {crnn.duration}")