import pyautogui
import win32gui
import win32con
import win32api
import tkcap
import tkinter as tk
import cv2
import pygetwindow as gw
import numpy as np
import time
from threading import Thread
from queue import Queue
from mss import mss
from PIL import Image
from translator import Translator
from textdetrec import TextDetectionRecognition
from torch.multiprocessing import Process

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"

class App:
    def __init__(self, w=400, h=200) -> None:
        # Root
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.window_centered(self.root,w,h)

        # Screenbox
        self.screenbox = None
        self.root_sbox_btn = tk.Button(self.root, text = 'Open Screenbox', bd = '5', command = self.__open_screenbox)
        self.root_sbox_btn.pack(anchor=tk.CENTER)

        # Queue
        self.flagqueue = Queue(1)
        self.valqueue = Queue(2)

        # Thread
        self.thread = Thread(target=self.detect_recognize_translate)
        self.thread.daemon = True

        # Screen capture
        self.sct = mss()
        self.captured_img = None

        # Detrec and translator
        self.detrec = TextDetectionRecognition(['en'])
        self.tl = Translator('id')

        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False
        self.capturemode = False
        self.pause = False
        self.inprocess = False

        # Create a canvas to display the captured image
        # Testing purpose, will be deleted
        self.canvas = tk.Canvas()
        self.canvas.pack()
        self.image = None
    
    def run(self) -> None:
        self.thread.start()
        self.root.mainloop()

    def __open_screenbox(self) -> None:
        if self.screenbox_open: return

        self.screenbox = tk.Toplevel(self.root)
        self.screenbox.title(SCREENBOX_NAME)
        # screenbox.overrideredirect(True)
        self.window_centered(self.screenbox,800,450)
        self.screenbox.attributes("-transparentcolor", "white",'-topmost',1)
        self.screenbox.config(bg="white")
        self.screenbox.protocol("WM_DELETE_WINDOW", self.__close_screenbox)

        self.screenbox.bind("d", self.__deletemode)
        self.screenbox.bind("c", lambda event: self.capture_toogle(event))

        self.screenbox_open = True

        # self.put_text(0, 0, "SIUUU")
        # self.put_text(100, 100, "SLEPET")

        self.capture_screen_mss()
        self.screenbox.mainloop()

    def capture_screen_pyautogui(self, event=None):
        # Credit to 'tkcap' for the reference
        x, y = self.screenbox.winfo_x() + 8, self.screenbox.winfo_y() + 30
        w, h = self.screenbox.winfo_width(), self.screenbox.winfo_height() + 8
        ss = np.array(pyautogui.screenshot(region=(x, y, w, h)).convert('RGB'))
        self.image = cv2.cvtColor(ss, cv2.COLOR_RGB2BGR)  

    def capture_toogle(self, event=None):
        self.pause = not self.pause

    def capture_screen_mss(self, event=None) -> None:
        # cv2.namedWindow("windowframe", cv2.WINDOW_NORMAL)
        print("[Process] Waiting...")
        if not self.flagqueue.empty():
            self.inprocess = self.flagqueue.get()
        if not self.pause and not self.inprocess:
            print("[Execute] Capture Screen.")
            x, y = self.screenbox.winfo_x() + 8, self.screenbox.winfo_y() + 30
            w, h = self.screenbox.winfo_width(), self.screenbox.winfo_height() + 8
            mon = {'top': y, 'left':x, 'width':w, 'height':h}

            sct_img = self.sct.grab(mon)
            img = Image.frombytes('RGB', (sct_img.size.width, sct_img.size.height), sct_img.rgb)

            self.captured_img = np.array(img)
            self.inprocess = True

            # img_bgr = cv2.cvtColor(self.captured_img, cv2.COLOR_RGB2BGR)
            # cv2.imshow('windowframe', np.array(img_bgr))
        # print("-----------------")
        if not self.valqueue.empty():
            boxtext = self.valqueue.get()
            for x in range(len(boxtext[0])):
                self.put_text(boxtext[0][x][0][0], boxtext[0][x][0][1], boxtext[1][x])
            
        self.screenbox.after(500, self.capture_screen_mss)

    def detect_recognize_translate(self):
        while True:
            if self.captured_img is not None:
                start = time.time()
                print("[Thread] OCR Process started")
                self.detrec.load_image_arr(self.captured_img)
                res = self.detrec.read()
                tled = self.tl.translate(text=self.tl.convert_to_string(res[1]))
                finaltl = tled[0].split('||')
                print("[-----------------------------]")
                print(res[0])
                print(finaltl)
                print(time.time() - start)
                print("[-----------------------------]\n")

                self.captured_img = None
                self.flagqueue.put(False)
                self.valqueue.put([res[0], finaltl])

    def __deletemode(self, event=None) -> None:
        if not self.screenbox_open: return
        if self.mode_deletemode:
            self.mode_deletemode = False
            self.screenbox.config(bg="white")
            self.screenbox.attributes('-alpha', 1)
        else:
            self.mode_deletemode = True
            self.screenbox.config(bg="gray")
            self.screenbox.attributes('-alpha', 0.4)

    def put_text(self, x, y, text) -> None:
        # Put a translated text into itw corresponding coordinate
        # Prototype
        
        textlabel = tk.Label(self.screenbox, text=text)
        textlabel.place(x=x,y=y)
        textlabel.bind("<Button-1>", lambda event: self.__destroy_text(event, textlabel))

    def __destroy_text(self, event, object) -> None:
        if not self.mode_deletemode: return
        object.destroy()

    def __close_screenbox(self) -> None:
        self.screenbox_open = False
        self.capturemode = False
        self.screenbox.destroy()

    def window_centered(self, window, w, h) -> None:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()

        x = (screen_w - w) // 2
        y = (screen_h - h) // 2

        window.geometry(f"{w}x{h}+{x}+{y}")

    def print_test(self, event=None) -> None:
        # Modify as needed
        print("Print Executed!")

if __name__ == '__main__':
    app = App()
    app.run()