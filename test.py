import tkinter as tk
import cv2
from PIL import Image, ImageTk
import time

root = tk.Tk()
root.attributes("-transparentcolor", "white")
root.config(bg="white")
root.geometry("1400x700")

imarr = cv2.imread("tests/fiekuro.jpg")     
converted = cv2.cvtColor(imarr, cv2.COLOR_BGR2RGB)           # OpenCV method
# lum = cv2.cvtColor(imarr, cv2.COLOR_RGB2HSV)[...,2]
# lum = cv2.cvtColor(imarr, cv2.COLOR_BGR2HLS)[...,1]
# cv2.imshow('windowframe', lum)
# lum_avg = cv2.mean(lum)
# print(lum_avg)
imglist: list[tk.PhotoImage] = []

def cn(x:int,y:int,w:int,h:int):
    cn = tk.Canvas(master=root, width=500, height=500, highlightthickness=0)
    converted = cv2.cvtColor(imarr[y:y+h, x:x+w], cv2.COLOR_BGR2RGB)
    img =  ImageTk.PhotoImage(image=Image.fromarray(converted))
    imglist.append(img)
    cn.create_image(0, 0, image = img, anchor = "nw")
    cn.create_text(0, 0, text="SIUUU", fill="#fffffe", 
                                font=('Helvetica', 30), 
                                anchor='nw')
    cn.place(x=x,y=y, width=w, height=h)

def c1():
    global g1
    c1 = tk.Canvas(master=root, width=500, height=500)
    g1 =  ImageTk.PhotoImage(image=Image.fromarray(imarr[0:500, 0:500]))

    c1.create_image(0, 0, image = g1, anchor = "nw")
    c1.create_text(0, 0, text="SIUUU", fill="#fffffe", 
                                font=('Helvetica', 30), 
                                anchor='nw')
    c1.place(x=0,y=0, width=500, height=500)
# --------------------------------------------------------
def c2():
    global g2
    c2 = tk.Canvas(master=root, width=500, height=500)
    g2 =  ImageTk.PhotoImage(image=Image.fromarray(imarr[500:1000, 500:1000]))

    c2.create_image(0, 0, image = g2, anchor = "nw")
    c2.create_text(0, 0, text="HIYAAA", fill="white", 
                                font=('Helvetica', 30), 
                                anchor='nw')
    c2.place(x=500,y=500, width=500, height=500)
# --------------------------------------------------------
def c3():
    global g3
    c3 = tk.Canvas(master=root, width=500, height=500)
    g3 =  ImageTk.PhotoImage(image=Image.fromarray(imarr[0:500, 500:1000]))

    c3.create_image(0, 0, image = g3, anchor = "nw")
    c3.create_text(0, 0, text="SPHHADSNO", fill="white", 
                                font=('Helvetica', 30), 
                                anchor='nw')
    c3.place(x=500,y=0, width=500, height=500)

# c1()
# c2()
# c3()

cn(0,0,500,500)
cn(500,500,500,500)
cn(500,0,500,500)

root.mainloop()