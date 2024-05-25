# import pyautogui
# import win32gui
# import win32con
# import win32api
# import tkcap
import asyncio
import tkinter as tk
import cv2
import numpy as np
import time
import requests
import ctypes
from threading import Thread
from tkinter import messagebox
from queue import Queue
from mss import mss
from PIL import Image, ImageTk
from lib.translator import GoogleTranslator
from lib.textdetrec import EasyOCRdetrec, WinOCRdetrec
from memory_profiler import profile
# from wscreenshot import Screenshot

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"
TRANSPARENT_COLOR = "#66cdab"

class TexTranslator:
    def __init__(self, w=400, h=400, src_lang="", target_lang="", detrec="easyocr") -> None:
        self.define_widgets(src_lang, target_lang, w=400, h=400)      # Tkinter widget init
        self.define_components(src_lang, detrec)    # Queue, Thread, Screen capture, EasyOCR, Tl init
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
        self.sbw = ctypes.windll.user32.GetSystemMetrics(0)
        self.sbh = ctypes.windll.user32.GetSystemMetrics(1)
        self.root_sbox_btn = tk.Button(self.root, text = 'Screenbox', bd = '4', command = self.select_area)
        self.root.bind("s", lambda event: self.keybind_openscreenbox(event))

        self.lang_list = ['en', 'ja', 'id', 'ru']
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
        self.root_ispgraph = tk.Checkbutton(self.root, text="Paragraph mode", variable=self.paragraphmode, onvalue=True, offvalue=False)
        self.maxscreen = tk.BooleanVar()
        self.root_ismaxscreen = tk.Checkbutton(self.root, text="Max screen mode", variable=self.maxscreen, onvalue=True, offvalue=False)

        self.changelang_light = tk.Button(self.root, bg="black", width=3)
        self.changelang_light.config(state="disabled")

    @profile
    def define_components(self, srclang:str, detrec:str) -> None:
        # Queue
        self.valqueue = Queue()

        # Screen capture
        self.sct = mss()
        self.captured_img = None
        self.last_captured = None
        self.bg_lists: list[tk.PhotoImage] = []

        # Detrec and translator
        langchoice = ['en'] if len(srclang) == 0 or srclang == 'en' else [self.lang_selected_src.get(),'en']
        if detrec == "winocr":
            print("Loading WinOCR configuration...")
            self.detrec = WinOCRdetrec(langchoice[0])
        elif detrec == "easyocr":
            print("Loading EasyOCR configuration...")
            self.detrec = EasyOCRdetrec(langchoice, use_gpu=True)
        self.drtype = detrec

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
        self.isplacingtext = False
        self.starttime = 0
        self.onchangelang = False
    
    def set_label_config(self) -> None:
        self.boxeslist: list
        self.textslist: list
        self.placedlabel: list[tk.Canvas] = []
        self.labelcount = 0
        self.labelplacingidx = 0
        self.fontdict = [0 for _ in range(90)]
        self.blurksize = 35
        self.fontsize_init()
    
    def apply_widget(self) -> None:
        self.root_sbox_btn.grid(column=0, row=0)
        self.srclang_lbl.grid(column=0, row=1)
        self.targetlang_lbl.grid(column=0, row=2)
        self.deletemode_btn.grid(column=1, row=0)
        self.language_menu_src.grid(column=1, row=1)
        self.language_menu_target.grid(column=1, row=2)
        self.root_ispgraph.grid(column=0,row=3)
        self.root_ismaxscreen.grid(column=0,row=4)
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
        self.select_area()

    def __open_screenbox(self) -> None:
        if self.screenbox_open: self.screenbox.destroy()

        self.screenbox = tk.Toplevel(self.root)
        self.screenbox.title(SCREENBOX_NAME)

        # Button organization
        btnframe = tk.Frame(self.screenbox, background=TRANSPARENT_COLOR)
        btnframe.pack(side="top", fill="x", anchor="n")
        self.machine_light = tk.Button(
            btnframe,
            bg="green", 
            width=5,
            command=self.capture_toogle
        )
        self.machine_light.pack(side="left")
        self.close_sb_btn = tk.Button(
            btnframe, 
            bg="yellow", 
            width=3,
            command=self.screenbox.destroy
        )
        self.close_sb_btn.pack(side="left")

        # Screenbox Configuration
        self.screenbox.overrideredirect(True)
        if self.maxscreen.get(): self.screenbox.state("zoomed")
        else: self.set_screenbox_position()
        
        self.screenbox.attributes("-transparentcolor", TRANSPARENT_COLOR,'-topmost',1)
        self.screenbox.config(bg=TRANSPARENT_COLOR)
        self.screenbox.protocol("WM_DELETE_WINDOW", self.__close_screenbox)

        # Screenbox keyboard binding
        self.screenbox.bind("d", self.__deletemode)
        self.screenbox.bind("c", lambda event: self.capture_toogle(event))
        self.screenbox.bind("v", lambda event: self.keybind_destroyalltext(event))

        self.screenbox_open = True
        
        self.sb_border = tk.Canvas(self.screenbox, bg=TRANSPARENT_COLOR)
        self.sb_border.pack(side="top", fill="both", expand=True)
        self.sb_border.create_rectangle(
            0, 0, 1, 1, 
            outline='#ffffff', 
            width=3
        )

        self.capture_screen_mss()
        self.starttime = time.time()
        self.screenbox.mainloop()
    
    def select_area(self):
        self.root.wm_state("iconic")
        if self.maxscreen.get(): self.__open_screenbox()
        self.overlay = tk.Toplevel(self.root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes('-alpha', 0.4)
        self.overlay.state("zoomed")
        self.overlaycanvas = tk.Canvas(self.overlay, bg="black")
        self.overlaycanvas.pack(side="top", fill="both", expand=True)
        self.overlaycanvas.bind("<Button-1>", self.__get_start_coor)
        self.overlaycanvas.bind("<ButtonRelease-1>", self.__get_end_coor)
        self.overlaycanvas.bind("<B1-Motion>", self.__drag_area)
    
    def __get_start_coor(self, event):
        self.__start_point = (event.x, event.y)
        self.area = self.overlaycanvas.create_rectangle(
            0, 0, 1, 1, 
            outline='#4fff38', 
            width=3
        )

    def __drag_area(self, event):
        self.overlaycanvas.coords(
            self.area, 
            self.__start_point[0], self.__start_point[1], 
            event.x, event.y
        )

    def __get_end_coor(self, event):
        self.__end_point = (event.x, event.y)
        self.overlay.destroy()
        self.__open_screenbox()

    def capture_toogle(self, event=None) -> None:
        self.pause = not self.pause
        color = "green" if self.pause else "red"
        self.machine_light.config(bg=color)

    def capture_screen_mss(self, event=None) -> None:
        if not self.valqueue.empty():
            boxestexts = self.valqueue.get()
            self.boxeslist = boxestexts[0]
            self.textslist = boxestexts[1]
            self.isplacingtext = True
        if self.isplacingtext and self.inprocess:
            try:
                self.put_text_2(
                    h=self.boxeslist[self.labelplacingidx][0],
                    w=self.boxeslist[self.labelplacingidx][1],
                    x=self.boxeslist[self.labelplacingidx][2],
                    y=self.boxeslist[self.labelplacingidx][3],
                    text=self.textslist[self.labelplacingidx]
                )
            except Exception as e:
                print("An exception occurred:", type(e).__name__, "–", e)
                self.closing_cycle()

        if not self.pause and not self.inprocess:
            print("[Execute] Capture Screen.")
            x, y = self.screenbox.winfo_x(), self.screenbox.winfo_y() -8
            w, h = self.screenbox.winfo_width(), self.screenbox.winfo_height()
            print(x, y)
            print(h, w)
            mon = {'top': y, 'left':x, 'width':w, 'height':h}

            sct_img = self.sct.grab(mon)
            img = Image.frombytes('RGB', (sct_img.size.width, sct_img.size.height), sct_img.rgb)

            self.captured_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            self.last_captured = self.captured_img.copy()
            self.inprocess = True

            # Thread
            thread = Thread(target=self.detect_recognize_translate)
            thread.daemon = True
            thread.start()

        self.screenbox.after(25, self.capture_screen_mss)

    def detect_recognize_translate(self):
        if self.captured_img is not None:
            print("[Thread] OCR Process started")
            print("[-----------------------------]")

            # Detection & recognition section
            self.detrec.load_image_arr(self.captured_img)
            res: list
            if self.drtype == 'winocr':
                res = self.detrec.read()
            elif self.drtype == 'easyocr':
                res = self.detrec.read(
                    wths=float(self.width_thres.get()),
                    pmode=self.paragraphmode.get(),
                    yths=float(self.y_thres.get()),    
                )
            elif self.drtype == 'paddleocr':
                res = self.detrec.read()
                print(self.detrec.detrectime)
            print(res)

            # # Text Translate section
            # asyncio.run(self.start_asynctl(res[0],res[1]))
            # translated = self.__easynmt_translate(texts=res[1])
            # translated = self.tl.translate(res[1])
            translated = res[1]
            
            self.valqueue.put([res[0],translated])
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
        converted = cv2.medianBlur(
            converted, self.blurksize, cv2.BORDER_REPLICATE
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
        self.labelplacingidx += 1
        canvas.update_idletasks()

        # check if all texts has been placed
        if self.labelcount == self.textcount: self.closing_cycle()

    def closing_cycle(self):
        self.pause = True
        self.machine_light.config(bg="green")
        self.isplacingtext = False
        self.inprocess = False
        self.labelplacingidx = 0

    def __det_textcolor(self, img):
        avglum = int(cv2.mean(
            cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:,:,2]
        )[0])
        return "#ffffff" if avglum <= 128 else "#000000"
    
    def __adjust_font_size(self, text:str, w:int, h:int) -> int:
        fontsize = int((h * (self.screenbox.winfo_height() * 1.25)) // self.dscreen_h)
        # if not self.paragraphmode.get(): fontsize = self.fontdict[h]-3
        if fontsize < 10 : fontsize = 15
        elif fontsize > 100 : fontsize = 75
        canvas = tk.Canvas()
        textid = canvas.create_text(0, 0, text=text, anchor='nw', width=w)
        
        while True:
            canvas.itemconfig(textid, font=('Bahnschrift', fontsize))
            bbox = canvas.bbox(textid)

            if bbox[3] - bbox[1] <= h: return fontsize
            if fontsize > 30: fontsize -= 5
            else: fontsize -= 1

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

    def set_screenbox_position(self) -> None:
        x1, y1 = self.__start_point
        x2, y2 = self.__end_point
        x, y = min(x1,x2), min(y1,y2)
        w = abs(x1-x2)
        h = abs(y1-y2)
        print(x,y)
        print(h,w)
        print("--------")
        self.screenbox.geometry(f"{w}x{h}+{x}+{y}")

if __name__ == '__main__':
    app = TexTranslator(
        src_lang='en', 
        target_lang='id', 
        detrec="winocr",
    )
    app.run()