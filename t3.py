import easyocr
import cv2
import time

reader = easyocr.Reader(['en'], detector=True)
img_path = "tests/rdm.jpg"
start = time.time()
res = reader.readtext(cv2.imread(img_path))
boxes = [item[0] for item in res]
texts = [item[1] for item in res]
newres = [boxes, texts]

# res = reader.readtext(
#     cv2.imread(img_path),
#     paragraph=True,
#     x_ths=0,
# )
# print("\n", time.time() - start)
for x in range(len(newres[0])):
    print(boxes[x][0])
    print("--------")