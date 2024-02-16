from sys import argv
import time
import cv2
import numpy as np
import shapely.geometry as spgeo
from imutils.object_detection import non_max_suppression

class EAST:
    FIXED_SIZE = 992
    def __init__(self, size = FIXED_SIZE) -> None:
        self.net = cv2.dnn.readNet("model/frozen_east_text_detection.pb")
        self.image = None
        self.original = None
        self.layer = [
            "feature_fusion/Conv_7/Sigmoid",
    	    "feature_fusion/concat_3"
        ]
        self.framesize = [size, size]

        self.box = []
        self.confident = []
        self.duration = 0.0
    
    def _load_image(self, imagepath) -> None:
        self.image = cv2.imread(imagepath)
        self.original = self.image.copy()
    
    def _to_rgb(self, img):
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        return img
    
    def _resize_image(self, img):
        return cv2.resize(
            img, (self.framesize[0],self.framesize[1])
        )

    def _detect(self):
        copy = self.image.copy()
        copy = self._to_rgb(copy)
        copy = self._resize_image(copy)
        (ori_h, ori_w) = self.image.shape[:2]
        (ratio_h, ratio_w) = (
            ori_h/float(self.framesize[0]),
            ori_w/float(self.framesize[1])
        )

        blob = cv2.dnn.blobFromImage(
            image       = copy, 
            scalefactor = 1.0, 
            size        = copy.shape[:2],
            mean        = (123.68, 116.78, 103.94), 
            swapRB      = True, 
            crop        = False
        )
        self.net.setInput(blob)
        
        (scores, geo) = self.net.forward(self.layer)

        (boxes, confidences) = self._decode_predictions(
            scores, 
            geo, 
            conf_threshold=0.5
        )
        boxes = non_max_suppression(
            np.array(boxes), 
            probs=confidences,
        )
        
        # boxes = self._merge_box(boxes)
        self._draw_predictions(
            boxes, ratio_h, ratio_w
        )
        
        return (self.image, boxes, (ratio_w, ratio_h))

    def _decode_predictions(self, scores, geo, conf_threshold):
        (scores_row, scores_col) = scores.shape[2:4]
        (boxes, confidences) = ([], [])
        for y in range(0, scores_row):
            scores_data = scores[0, 0, y]
            x_data0 = geo[0, 0, y]
            x_data1 = geo[0, 1, y]
            x_data2 = geo[0, 2, y]
            x_data3 = geo[0, 3, y]
            angles_data = geo[0, 4, y]

            for x in range(0, scores_col):
                curr_score = scores_data[x]
                if curr_score < conf_threshold:
                    continue

                (offset_x, offset_y) = (x * 4.0, y * 4.0)

                angle = angles_data[x]
                (cos_a, sin_a) = (
                    np.cos(angle), 
                    np.sin(angle)
                )

                box_h = x_data0[x] + x_data2[x]
                box_w = x_data1[x] + x_data3[x]

                ex = int(offset_x + (cos_a * x_data1[x]) + (sin_a * x_data2[x]))
                ey = int(offset_y - (sin_a * x_data1[x]) + (cos_a * x_data2[x]))
                sx = int(ex - box_w)
                sy = int(ey - box_h)

                boxes.append((sx, sy, ex+1, ey+4))
                confidences.append(float(curr_score))

        return boxes, confidences
    
    def _merge_box(self, boxes: list[tuple]):
        print(boxes)
        clusters = [boxes[0]]
        for i in range(1,len(boxes)):
            for x in range(0, len(clusters)):
                if self.__is_geo_intersect(clusters[x], boxes[i]):
                    x1 = min(clusters[x][0], boxes[i][0])
                    x2 = min(clusters[x][1], boxes[i][1])
                    x3 = max(clusters[x][2], boxes[i][2])
                    x4 = max(clusters[x][3], boxes[i][3])
                    clusters[x] = (x1, x2, x3, x4)
                    break
                else:
                    clusters.append(boxes[i])
                    
        return clusters

    def __is_geo_intersect(self, a, b) -> bool:
        x1a, y1a, x2a, y2a = a
        x1b, y1b, x2b, y2b = b
        rule1 = (x1a >= x1b and x1a <= x2b) or (x2a >= x1b and x2a <= x2b)
        rule2 = (y1a >= y1b and y1a <= y2b) or (y2a >= y1b and y2a <= y2b)
        return rule1 and rule2

    def _draw_predictions(self, boxes, hratio, wratio):
        for (sx, sy, ex, ey) in boxes:
            cv2.rectangle(
                self.image,
                (int(wratio * sx),int(hratio * sy)),
                (int(wratio * ex),int(hratio * ey)),
                (0, 255, 0), 
                1
            )
    def exec(self, imagepath):
        start = time.time()
        self._load_image(imagepath)
        (result, boxes, ratio) = self._detect()
        self.duration = time.time() - start

        cv2.imwrite("detection_res.jpg", self.image)
        return result, boxes, ratio