import pytesseract
import time
import cv2
from detection import EAST

# Provide the path to the Tesseract executable (change this to match your installation)
pytesseract.pytesseract.tesseract_cmd = r'C:/storagedrive/ITB/Learn/Sem7/TA1/Laporan/Tesseract-OCR/tesseract.exe'

east = EAST()
detect_map, boxes, ratio = east.exec("tests/mic.jpg")
word_list = []

start = time.time()
def recognize_word(box, ori, ratio):
    a, b, c, d = box
    a = int(ratio[0]*a)
    b = int(ratio[1]*b)
    c = int(ratio[0]*c)
    d = int(ratio[1]*d)
    cropped = ori[b:d,a:c]
    text = pytesseract.image_to_string(cropped)
    # print("\nLocation: ", a, b, c, d)
    print("Recognition duration: ", text)
    # print("Extracted Text: ", text)
    word_list.append(text)

for box in boxes:
    recognize_word(box, east.original, ratio)

finish = time.time()-start
print(word_list)

cv2.imwrite("detection_res2.jpg", detect_map)

print(f"\nDetection duration = {east.duration}")
print(f"Recognition duration = {finish}")