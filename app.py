# import pyautogui
# import win32gui
# import win32con
# import win32api
# import tkcap
import tkinter as tk
# import cv2
import pygetwindow as gw
import numpy as np
import time
from threading import Thread
from tkinter import messagebox
from queue import Queue
from mss import mss
from PIL import Image
from translator import Translator
from textdetrec import TextDetectionRecognition
from torch.multiprocessing import Process

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"

class App:
    def __init__(self, w=300, h=400) -> None:
        # Root
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.dscreen_w = self.root.winfo_screenwidth()
        self.dscreen_h = self.root.winfo_screenheight()
        self.window_centered(self.root,w,h)

        self.screenbox = None
        self.sbw = 500
        self.sbh = 250
        self.root_sbox_btn = tk.Button(self.root, text = 'Screenbox', bd = '4', command = self.__open_screenbox)
        self.root_sbox_light = tk.Button(self.root, bg="red", width=3)
        self.root_sbox_light.config(state="disabled")
        

        lang_list = ['en', 'ja', 'id']
        self.lang_selected_src = tk.StringVar()
        self.lang_selected_src.set(lang_list[0])
        self.lang_selected_target = tk.StringVar()
        self.lang_selected_target.set(lang_list[2])
        language_menu_src = tk.OptionMenu(self.root, self.lang_selected_src, *lang_list, command = self.onchange_srclang)
        srclang_lbl = tk.Label(self.root, text="Source Language")
        targetlang_lbl = tk.Label(self.root, text="Target Language")
        language_menu_target = tk.OptionMenu(self.root, self.lang_selected_target, *lang_list)
        

        self.sb_size = tk.StringVar(self.root, "700x450")
        self.sizeslist = ("400x300", "700x450", "1000x600", "1300x750")
        self.paragraphmode = tk.BooleanVar()
        self.gpumode = tk.BooleanVar()
        self.root_ispgraph = tk.Checkbutton(self.root, text="Paragraph mode", variable=self.paragraphmode, onvalue=True, offvalue=False)
        self.root_usegpu = tk.Checkbutton(self.root, text="GPU mode", variable=self.gpumode, onvalue=True, offvalue=False)
        
        # Queue
        self.valqueue = Queue(1)

        # Thread
        self.thread = Thread(target=self.detect_recognize_translate)
        self.thread.daemon = True

        # Screen capture
        self.sct = mss()
        self.captured_img = None

        # Detrec and translator
        self.detrec = TextDetectionRecognition(['en', 'ja'])
        self.tl = Translator(self.lang_selected_target.get())

        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False
        self.capturemode = False
        self.pause = True
        self.inprocess = False

        self.placedlabel: list[tk.Label] = []

        self.root_sbox_btn.grid(column=0, row=0, columnspan=2)
        self.root_sbox_light.grid(column=2, row=0)
        srclang_lbl.grid(column=0, row=1)
        targetlang_lbl.grid(column=0, row=2)
        language_menu_src.grid(column=1, row=1)
        language_menu_target.grid(column=1, row=2)
        self.root_ispgraph.grid(column=0,row=3)
        self.root_usegpu.grid(column=0,row=4)
        for x in range(len(self.sizeslist)):
            r = tk.Radiobutton(
                self.root,
                text=self.sizeslist[x],
                value=self.sizeslist[x],
                variable=self.sb_size
            )
            r.grid(column=1, row=3+x)
    
    def run(self) -> None:
        self.thread.start()
        self.root.mainloop()
    
    def onchange_srclang(self, *args) -> None:
        # Code still not supported multi language
        # messagebox.showinfo("Info", "Please wait... (DON'T CLICK ANYTHING)")
        thread = Thread(target=self.detrec.lang_change, args=([self.lang_selected_src.get()],))
        thread.start()
        print("LEWAT")

    def __set_screenbox_size(self) -> None:
        sbw: int
        sbh: int
        if self.sb_size.get() == self.sizeslist[0]: sbw, sbh = (400, 300)
        elif self.sb_size.get() == self.sizeslist[1]: sbw, sbh = (700, 450)
        elif self.sb_size.get() == self.sizeslist[2]: sbw, sbh = (1000, 600)
        elif self.sb_size.get() == self.sizeslist[3]: sbw, sbh = (1300, 750)
        self.sbw = sbw
        self.sbh = sbh

    def __open_screenbox(self) -> None:
        if self.screenbox_open: return

        self.screenbox = tk.Toplevel(self.root)
        self.screenbox.title(SCREENBOX_NAME)
        # screenbox.overrideredirect(True)
        self.__set_screenbox_size()
        self.window_centered(self.screenbox,self.sbw,self.sbh)
        self.screenbox.resizable(False, False)
        self.screenbox.attributes("-transparentcolor", "white",'-topmost',1)
        self.screenbox.config(bg="white")
        self.screenbox.protocol("WM_DELETE_WINDOW", self.__close_screenbox)

        self.screenbox.bind("d", self.__deletemode)
        self.screenbox.bind("c", lambda event: self.capture_toogle(event))

        self.screenbox_open = True

        self.capture_screen_mss()
        self.screenbox.mainloop()

    def capture_toogle(self, event=None) -> None:
        self.pause = not self.pause
        color = "red" if self.pause else "green"
        self.root_sbox_light.config(bg=color)

    def capture_screen_mss(self, event=None) -> None:
        if not self.valqueue.empty():
            try:
                boxtext = self.valqueue.get()
                print("boxtext len: ", len(boxtext[0]))
                for x in range(len(boxtext[0])):
                    self.put_text(
                        x=boxtext[0][x][0][0], 
                        y=boxtext[0][x][0][1],
                        w=boxtext[0][x][2][0]-boxtext[0][x][0][0],
                        h=boxtext[0][x][2][1]-boxtext[0][x][0][1],
                        text=boxtext[1][x]
                    )
            except Exception as e:
                print("[error] ", e, "\n")
            finally:
                # !! FOR DEVELOPMENT ONLY
                self.pause = True
                self.root_sbox_light.config(bg="red")
                self.inprocess = False
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
            
        self.screenbox.after(500, self.capture_screen_mss)

    def detect_recognize_translate(self):
        while True:
            if self.captured_img is not None:
                print("[Thread] OCR Process started")
                start = time.time()
                self.detrec.load_image_arr(self.captured_img)
                # print("self.paragraphmode : ", self.paragraphmode.get())
                res = self.detrec.read(
                    pmode=self.paragraphmode.get(),
                    yths=0.6,    
                )
                finaltl = self.tl.translate(texts=res[1])
                print("[-----------------------------]")
                print("detrec + tr time: ", time.time() - start)
                print(res[1])
                print(finaltl)
                print("[-----------------------------]\n")

                self.captured_img = None
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

    def put_text(self, x, y, w, h, text) -> None:
        # Put a translated text into itw corresponding coordinate
        # Need extensive customization in tkinter app side
        # - width
        # - width ths
        # - paragraph true / false
        # etc. try tinkering the documentation
        
        # fontsize = ((h - 6) * (self.screenbox.winfo_height() + 8)) // self.dscreen_h
        textlabel = tk.Label(self.screenbox, text=text, width=w+120, wraplength=w, justify="left")
        textlabel.place(x=x,y=y-10, width=w, height=h)
        textlabel.bind("<Button-1>", lambda event: self.__destroy_text(event, textlabel))

        self.placedlabel.append(textlabel)

    def __destroy_text(self, event, object) -> None:
        if not self.mode_deletemode: return
        object.destroy()
    
    def __destroy_all_text(self) -> None:
        self.placedlabel = [l.destroy() for l in self.placedlabel]
        self.placedlabel = []

    def __close_screenbox(self) -> None:
        self.screenbox_open = False
        self.capturemode = False
        self.mode_deletemode = False
        self.pause = True
        self.inprocess = False
        if len(self.placedlabel) != 0:
            self.__destroy_all_text()
        self.screenbox.destroy()

    def window_centered(self, window:tk.Tk, w, h) -> None:
        x = (self.dscreen_w - w) // 2
        y = (self.dscreen_h - h) // 2

        window.geometry(f"{w}x{h}+{x}+{y}")

if __name__ == '__main__':
    app = App()
    app.run()