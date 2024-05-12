# import pyautogui
# import win32gui
# import win32con
# import win32api
# import tkcap
import asyncio
import tkinter as tk
import cv2
import pygetwindow as gw
import numpy as np
import time
import torch
import requests
from threading import Thread
from tkinter import messagebox
from queue import Queue
from mss import mss
from PIL import Image, ImageTk, ImageFilter
from translator import EasyNMTranslator, GoogleTranslator
from textdetrec import TextDetectionRecognition
from torch.multiprocessing import Process

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"
TRANSPARENT_COLOR = "#66cdab"

class TexTranslator:
    def __init__(self, w=400, h=400, src_lang="", target_lang="", translator="Google") -> None:
        self.define_widgets(src_lang, target_lang, w=400, h=400)      # Tkinter widget init
        self.define_components(src_lang, translator)    # Queue, Thread, Screen capture, EasyOCR, Tl init
        self.define_flags()                             # Flags init
        self.set_label_config()                         # Label-related setup
        self.apply_widget()                             # Put every widget in grid

    def define_widgets(self, srclang:str, targetlang:str, w=400, h=400) -> None:
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
        self.root.bind("s", lambda event: self.keybind_openscreenbox(event))

        self.lang_list = ['en', 'ja', 'id']
        self.lang_selected_src = tk.StringVar()
        self.lang_selected_src.set(srclang)
        self.lang_selected_target = tk.StringVar()
        self.lang_selected_target.set(targetlang)
        self.language_menu_src = tk.OptionMenu(self.root, self.lang_selected_src, *self.lang_list, command = self.set_language_flag)
        self.srclang_lbl = tk.Label(self.root, text="Source Language")
        self.targetlang_lbl = tk.Label(self.root, text="Target Language")
        self.language_menu_target = tk.OptionMenu(self.root, self.lang_selected_target, *self.lang_list)
        self.deletemode_btn = tk.Button(self.root, text="Delete Mode", bd="4", command=self.__deletemode)

        self.sb_size = tk.StringVar(self.root, "700x450")
        self.width_thres = tk.StringVar(self.root, "0.7")
        self.y_thres = tk.StringVar(self.root, "0.6")
        self.sizeslist = ("400x300", "700x450", "1000x600", "1300x750")
        self.paragraphmode = tk.BooleanVar()
        self.gpumode = tk.BooleanVar()
        self.root_ispgraph = tk.Checkbutton(self.root, text="Paragraph mode", variable=self.paragraphmode, onvalue=True, offvalue=False)
        # self.root_usegpu = tk.Checkbutton(self.root, text="GPU mode", variable=self.gpumode, onvalue=True, offvalue=False)

        self.changelang_light = tk.Button(self.root, bg="black", width=3)
        self.changelang_light.config(state="disabled")

    def define_components(self, srclang:str, tl:str) -> None:
        # Queue
        self.valqueue = Queue()

        # Thread
        self.detrecthread = Thread(target=self.detect_recognize_translate)
        self.detrecthread.daemon = True

        # Screen capture
        self.sct = mss()
        self.captured_img = None
        self.last_captured = None
        self.bg_lists: list[tk.PhotoImage] = []

        # Detrec and translator
        langchoice = ['en'] if len(srclang) == 0 or srclang == 'en' else ['en', self.lang_selected_src.get()]
        print("Loading Detection & Recognition model EasyOCR...")
        self.detrec = TextDetectionRecognition(langchoice, use_gpu=True)

        if tl == "EasyNMT":
            print("Loading Translation model EasyNMT...")
            self.tl = EasyNMTranslator(
                self.lang_selected_src.get(),
                self.lang_selected_target.get()
            )
        elif tl == "Google":
            print("Loading Translation model GoogleTranslator...")
            self.tl = GoogleTranslator(
                self.lang_selected_src.get(),
                self.lang_selected_target.get()
            )
        print("Models loading completed!")
        print("Starting TexTranslator App...")
    
    def define_flags(self) -> None:
        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False
        self.capturemode = False
        self.pause = True
        self.inprocess = False
        self.starttime = 0
        self.onchangelang = False
    
    def set_label_config(self) -> None:
        self.placedlabel: list[tk.Canvas] = []
        self.labelcount = 0
        self.fontdict = [0 for _ in range(90)]
        self.fontsize_init()
    
    def apply_widget(self) -> None:
        self.root_sbox_btn.grid(column=0, row=0)
        self.srclang_lbl.grid(column=0, row=1)
        self.targetlang_lbl.grid(column=0, row=2)
        self.deletemode_btn.grid(column=1, row=0)
        self.language_menu_src.grid(column=1, row=1)
        self.language_menu_target.grid(column=1, row=2)
        self.root_ispgraph.grid(column=0,row=3)
        # self.root_usegpu.grid(column=0,row=4)
        self.changelang_light.grid(column=2, row=1)
        for x in range(len(self.sizeslist)):
            r = tk.Radiobutton(
                self.root,
                text=self.sizeslist[x],
                value=self.sizeslist[x],
                variable=self.sb_size
            )
            r.grid(column=1, row=3+x)
    
    def run(self) -> None:
        self.detrecthread.start()
        self.root.mainloop()
    
    def fontsize_init(self) -> None:
        cn = tk.Canvas(self.root)
        limit = 0
        for x in range (8,51):
            textid = cn.create_text(0,0,text="Tl",font=('Bahnschrift', x))
            box = cn.bbox(textid)
            i = box[3]-box[1]
            while i >= limit:
                self.fontdict[i] = x
                i -= 1
            limit = box[3]-box[1]

    def set_language_flag(self, event=None):
        self.onchangelang = True
        self.changelang_light.config(bg="blue")
        self.change_srclang()
    
    def change_srclang(self):
        if self.onchangelang:
            print("Change Language...")
            messagebox.showinfo("Info", "Please keep away from clicking anything on this app until the next notification. Click 'OK' to start change language.")
            self.detrec.lang_change(self.lang_selected_src.get())
            self.onchangelang = False
            messagebox.showinfo("Info", "Change language completed!")
            self.changelang_light.config(bg="black")

    def __set_screenbox_size(self) -> None:
        sbw: int
        sbh: int
        if self.sb_size.get() == self.sizeslist[0]: sbw, sbh = (400, 300)
        elif self.sb_size.get() == self.sizeslist[1]: sbw, sbh = (700, 450)
        elif self.sb_size.get() == self.sizeslist[2]: sbw, sbh = (1000, 600)
        elif self.sb_size.get() == self.sizeslist[3]: sbw, sbh = (1300, 750)
        self.sbw = sbw
        self.sbh = sbh

    def keybind_openscreenbox(self, event) -> None:
        self.__open_screenbox()

    def __open_screenbox(self) -> None:
        if self.screenbox_open: return

        self.screenbox = tk.Toplevel(self.root)
        self.screenbox.title(SCREENBOX_NAME)
        self.machine_light = tk.Button(self.screenbox, bg="green", width=3)
        self.machine_light.config(state="disabled")
        self.machine_light.pack(anchor="ne")

        # screenbox.overrideredirect(True)
        self.__set_screenbox_size()
        self.window_centered(self.screenbox,self.sbw,self.sbh)
        # self.screenbox.resizable(False, False)
        self.screenbox.attributes("-transparentcolor", TRANSPARENT_COLOR,'-topmost',1)
        self.screenbox.config(bg=TRANSPARENT_COLOR)
        self.screenbox.protocol("WM_DELETE_WINDOW", self.__close_screenbox)

        self.screenbox.bind("d", self.__deletemode)
        self.screenbox.bind("c", lambda event: self.capture_toogle(event))
        self.screenbox.bind("v", lambda event: self.keybind_destroyalltext(event))

        self.screenbox_open = True

        self.capture_screen_mss()
        self.starttime = time.time()
        self.screenbox.mainloop()

    def capture_toogle(self, event=None) -> None:
        self.pause = not self.pause
        color = "green" if self.pause else "red"
        self.machine_light.config(bg=color)

    def capture_screen_mss(self, event=None) -> None:
        if not self.valqueue.empty() and self.inprocess:
            try:
                boxtext = self.valqueue.get()
                start = time.time()
                for i in range(len(boxtext[0])):
                    self.put_text_2(
                        h=boxtext[0][i][0],
                        w=boxtext[0][i][1],
                        x=boxtext[0][i][2],
                        y=boxtext[0][i][3],
                        text=boxtext[1][i]
                    )
                print("Label placing time: ", time.time()-start)
            except Exception as e:
                print("[error] ", e, "\n")
                self.closing_cycle()

        if not self.pause and not self.inprocess:
            print("[Execute] Capture Screen.")
            x, y = self.screenbox.winfo_x() + 8, self.screenbox.winfo_y() + 30
            w, h = self.screenbox.winfo_width(), self.screenbox.winfo_height() + 8
            mon = {'top': y, 'left':x, 'width':w, 'height':h}

            sct_img = self.sct.grab(mon)
            img = Image.frombytes('RGB', (sct_img.size.width, sct_img.size.height), sct_img.rgb)

            self.captured_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            self.last_captured = self.captured_img.copy()
            self.inprocess = True
        self.screenbox.after(100, self.capture_screen_mss)

    def detect_recognize_translate(self):
        while True:
            if self.captured_img is not None:
                print("[Thread] OCR Process started")
                print("[-----------------------------]")

                # Detection & recognition section
                self.detrec.load_image_arr(self.captured_img)
                res = self.detrec.read(
                    wths=float(self.width_thres.get()),
                    pmode=self.paragraphmode.get(),
                    yths=float(self.y_thres.get()),    
                )
                print(res)

                # # Text Translate section
                # asyncio.run(self.start_asynctl(res[0],res[1]))
                # translated = self.__easynmt_translate(texts=res[1])
                # translated = self.tl.translate(res[1])
                translated = res[1]

                # Bounding-box parsing to (h, w, x, y)
                finalboxes = []
                for i in range(len(res[0])):
                    h = int(res[0][i][2][1]-res[0][i][0][1])
                    w = int(res[0][i][2][0]-res[0][i][0][0])
                    x = int(res[0][i][0][0])
                    y = int(res[0][i][0][1])
                    finalboxes.append([h,w,x,y])
                
                self.valqueue.put([finalboxes,translated])
                self.textcount = len(res[0])
                self.captured_img = None
                self.tl.show_tr_duration()
                print("[-----------------------------]\n")
    
    async def start_asynctl(self, boxes:list[list], texts:list[str]):
        url = "https://c307-34-143-249-81.ngrok-free.app/"
        start = time.time()
        response = requests.post(url,
                json={'target_lang': self.lang_selected_target.get(), 'text': texts})
        print(time.time()-start)
        idx = 0
        for tled in response.json():
            self.valqueue.put([boxes[idx], tled])
            idx += 1

    def __easynmt_translate(self, texts:list[str]):
        url = "https://4bff-34-125-31-126.ngrok-free.app/"
        start = time.time()
        response = requests.post(url,
                json={'target_lang': self.lang_selected_target.get(), 'text': texts})
        print(time.time()-start)
        return response.json()

    def __deletemode(self, event=None) -> None:
        if not self.screenbox_open: return
        if self.mode_deletemode:
            self.mode_deletemode = False
            self.screenbox.config(bg=TRANSPARENT_COLOR)
            self.screenbox.attributes('-alpha', 1)
        else:
            self.mode_deletemode = True
            self.screenbox.config(bg="gray")
            self.screenbox.attributes('-alpha', 0.4)

    def put_text_2(self, x, y, w, h, text) -> None:
        # determine fontsize
        fontsize = self.__adjust_font_size(text,w,h)
        canvas = tk.Canvas(self.screenbox, width=w, height=h, highlightthickness=0)
        
        # crop an image and manipulate it as background
        cropped = self.last_captured[y:y+h, x:x+w]
        converted = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        ksize = (11,11)
        converted = cv2.blur(
            cv2.medianBlur(
                converted, 13, cv2.BORDER_REPLICATE
            ), ksize, cv2.BORDER_REPLICATE
        )

        # create an ImageTk for displayinh
        bg = ImageTk.PhotoImage(
            image=Image.fromarray(converted)
        )
        self.bg_lists.append(bg)

        # draw text to canvas
        canvas.create_image(0, 0, image = bg, anchor = "nw")
        textid = canvas.create_text(0, 0, text=text, fill=self.__det_textcolor(converted), 
                             font=('Bahnschrift', fontsize), 
                             anchor='nw')
        if self.paragraphmode: canvas.itemconfig(textid, width=w)
        canvas.place(x=x,y=y-10, width=w, height=h)
        canvas.bind("<Button-1>", lambda event: self.__destroy_text(event, canvas))

        # placed text calculation
        self.placedlabel.append(canvas)
        self.labelcount += 1
        canvas.update_idletasks()

        # check if all texts has been placed
        if self.labelcount == self.textcount: self.closing_cycle()

    def closing_cycle(self):
        self.pause = True
        self.machine_light.config(bg="green")
        self.inprocess = False

    def __det_textcolor(self, img):
        avglum = int(cv2.mean(
            cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:,:,2]
        )[0])
        return "#ffffff" if avglum <= 128 else "#000000"
    
    def __adjust_font_size(self, text:str, w:int, h:int) -> int:
        fontsize = int((h * (self.screenbox.winfo_height() * 1.25)) // self.dscreen_h)
        if not self.paragraphmode.get(): fontsize = self.fontdict[h]-3
        if fontsize < 10 : fontsize = 15
        elif fontsize > 70 : fontsize = 50
        canvas = tk.Canvas()
        textid = canvas.create_text(0, 0, text=text, anchor='nw', width=w)
        
        while True:
            canvas.itemconfig(textid, font=('Bahnschrift', fontsize))
            bbox = canvas.bbox(textid)

            if bbox[3] - bbox[1] <= h: return fontsize
            if fontsize > 25: fontsize -= 10
            else: fontsize -= 2

    def __destroy_text(self, event, object) -> None:
        if not self.mode_deletemode: return
        object.destroy()
        self.labelcount -= 1
    
    def __destroy_all_text(self) -> None:
        if self.labelcount != 0: self.placedlabel = [l.destroy() for l in self.placedlabel]
        self.placedlabel = []
        self.labelcount = 0
    
    def keybind_destroyalltext(self, event) -> None:
        self.__destroy_all_text()

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
    app = TexTranslator(
        src_lang='en', 
        target_lang='id', 
        translator="Google"
    )
    app.run()