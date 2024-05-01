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
from threading import Thread
from tkinter import messagebox
from queue import Queue
from mss import mss
from PIL import Image, ImageTk, ImageFilter
from translator import Translator
from textdetrec import TextDetectionRecognition
from torch.multiprocessing import Process

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"
TRANSPARENT_COLOR = "#66cdab"

class App:
    def __init__(self, w=400, h=400, src_lang="", target_lang="") -> None:
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
        

        lang_list = ['en', 'ja', 'id']
        self.lang_selected_src = tk.StringVar()
        self.lang_selected_src.set(src_lang)
        self.lang_selected_target = tk.StringVar()
        self.lang_selected_target.set(target_lang)
        # language_menu_src = tk.OptionMenu(self.root, self.lang_selected_src, *lang_list, command = self.onchange_srclang)
        # srclang_lbl = tk.Label(self.root, text="Source Language")
        # targetlang_lbl = tk.Label(self.root, text="Target Language")
        # language_menu_target = tk.OptionMenu(self.root, self.lang_selected_target, *lang_list)
        deletemode_btn = tk.Button(self.root, text="Delete Mode", bd="4", command=self.__deletemode)

        self.sb_size = tk.StringVar(self.root, "700x450")
        self.width_thres = tk.StringVar(self.root, "0.7")
        self.y_thres = tk.StringVar(self.root, "0.6")
        self.sizeslist = ("400x300", "700x450", "1000x600", "1300x750")
        self.paragraphmode = tk.BooleanVar()
        self.gpumode = tk.BooleanVar()
        self.root_ispgraph = tk.Checkbutton(self.root, text="Paragraph mode", variable=self.paragraphmode, onvalue=True, offvalue=False)
        # self.root_usegpu = tk.Checkbutton(self.root, text="GPU mode", variable=self.gpumode, onvalue=True, offvalue=False)
        
        # Queue
        self.valqueue = Queue(5)

        # Thread
        self.thread = Thread(target=self.detect_recognize_translate)
        self.thread.daemon = True

        # Screen capture
        self.sct = mss()
        self.captured_img = None
        self.last_captured = None
        self.bg_lists: list[tk.PhotoImage] = []

        # Detrec and translator
        langchoice = ['en'] if len(src_lang) == 0 or src_lang == 'en' else ['en', self.lang_selected_src.get()]
        self.detrec = TextDetectionRecognition(langchoice, use_gpu=True)
        self.tl = Translator(self.lang_selected_target.get())

        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False
        self.capturemode = False
        self.pause = True
        self.inprocess = False

        self.placedlabel: list[tk.Canvas] = []
        self.labelcount = 0

        self.root_sbox_btn.grid(column=0, row=0)
        # srclang_lbl.grid(column=0, row=1)
        # targetlang_lbl.grid(column=0, row=2)
        deletemode_btn.grid(column=1, row=0)
        # language_menu_src.grid(column=1, row=1)
        # language_menu_target.grid(column=1, row=2)
        self.root_ispgraph.grid(column=0,row=3)
        # self.root_usegpu.grid(column=0,row=4)
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
    
    def onchange_srclang(self, *args) -> str:
        # Code still not supported multi language
        # messagebox.showinfo("Info", "Please wait... (DON'T CLICK ANYTHING)")
        # thread = Thread(target=self.detrec.lang_change, args=([self.lang_selected_src.get()],))
        # thread.start()
        self.root.destroy()

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
        self.machine_light = tk.Button(self.screenbox, bg="red", width=3)
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
        self.screenbox.mainloop()

    def capture_toogle(self, event=None) -> None:
        self.pause = not self.pause
        color = "red" if self.pause else "green"
        self.machine_light.config(bg=color)

    def capture_screen_mss(self, event=None) -> None:
        if not self.valqueue.empty():
            try:
                boxtext = self.valqueue.get()
                print(boxtext)
                self.put_text_2(
                    x=boxtext[0][0][0], 
                    y=boxtext[0][0][1],
                    w=boxtext[0][2][0]-boxtext[0][0][0],
                    h=boxtext[0][2][1]-boxtext[0][0][1],
                    text=boxtext[1]
                )
            except Exception as e:
                print("[error] ", e, "\n")

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

            # img_bgr = cv2.cvtColor(self.captured_img, cv2.COLOR_RGB2BGR)
            # cv2.imshow('windowframe', np.array(img_bgr))
            
        self.screenbox.after(500, self.capture_screen_mss)

    def detect_recognize_translate(self):
        while True:
            if self.captured_img is not None:
                print("[Thread] OCR Process started")
                print("[-----------------------------]")
                start = time.time()
                self.detrec.load_image_arr(self.captured_img)
                res = self.detrec.read(
                    wths=float(self.width_thres.get()),
                    pmode=self.paragraphmode.get(),
                    yths=float(self.y_thres.get()),    
                )
                print("detrec time: ", time.time() - start)
                asyncio.run(self.start_asynctl(res[0],res[1]))

                self.captured_img = None
                self.pause = True
                self.machine_light.config(bg="red")
                self.inprocess = False
                print("[-----------------------------]\n")
    
    async def start_asynctl(self, boxes:list[list], texts:list[str]):
        idx = 0
        start = time.time()
        async for tled in self.tl.asynctranslate(texts):
            self.valqueue.put([boxes[idx], tled])
            idx += 1
        print("tr time: ", time.time()-start)

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
        # Put a translated text into itw corresponding coordinate
        # Need extensive customization in tkinter app side
        # - width
        # - width ths
        # - paragraph true / false
        # etc. try tinkering the documentation
        fontsize = self.__adjust_font_size(text,w,h)
        canvas = tk.Canvas(self.screenbox, width=w, height=h, highlightthickness=0)
        cropped = self.last_captured[y:y+h, x:x+w]
        converted = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        ksize = (11,11)
        converted = cv2.blur(
            cv2.medianBlur(
                converted, 13, cv2.BORDER_REPLICATE
            ), ksize, cv2.BORDER_REPLICATE
        )
        bg = ImageTk.PhotoImage(
            image=Image.fromarray(converted)
        )
        self.bg_lists.append(bg)

        canvas.create_image(0, 0, image = bg, anchor = "nw")
        canvas.create_text(0, 0, text=text, fill=self.__det_textcolor(converted), 
                             font=('Helvetica', fontsize), 
                             anchor='nw', width=w)
        canvas.place(x=x,y=y-10, width=w, height=h)
        canvas.bind("<Button-1>", lambda event: self.__destroy_text(event, canvas))

        self.placedlabel.append(canvas)
        self.labelcount += 1

    def __det_textcolor(self, img):
        avglum = int(cv2.mean(
            cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:,:,2]
        )[0])
        return "#ffffff" if avglum <= 128 else "#000000"
    
    def __adjust_font_size(self, text:str, w:int, h:int) -> int:
        fontsize = int((h * (self.screenbox.winfo_height() * 1.25)) // self.dscreen_h)
        if fontsize < 10 : fontsize = 15
        elif fontsize > 100 : fontsize = 100
        canvas = tk.Canvas(self.screenbox)
        while True:
            textid = canvas.create_text(0, 0, text=text, fill="black", 
                                font=('Helvetica', fontsize), 
                                anchor='nw')
            bbox = canvas.bbox(textid)
            # print("fontsize ", fontsize, ": ", bbox, " -- ", w)
            if bbox[2]-bbox[0] <= w and bbox[3] - bbox[1] <= h: return fontsize
            textid = canvas.create_text(0, 0, text=text, font=('Helvetica', fontsize), anchor='nw', width=w)
            bbox = canvas.bbox(textid)

            if bbox[3] - bbox[1] <= h: return fontsize
            if fontsize > 33: fontsize -= 10
            else: fontsize -= 3

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
    app = App(src_lang='ja', target_lang='id')
    app.run()
    # launcher_active = True

    # print("[--TexTranslator--]")
    # while launcher_active:
    #     print("Source Language: ", end="")
    #     srclang = input()
    #     print("Translated Language: ", end="")
    #     tledlang = input()

    #     app = App(src_lang=srclang, target_lang=tledlang)
    #     app.run()  # Activate Tkinter GUI using root.mainloop()

    #     # Check if user wants to quit or restart language selection
    #     choice = input("Do you want to quit (q) or restart language selection (r)? ")
    #     if choice.lower() == 'q':
    #         launcher_active = False  # Exit the loop to quit
    #     elif choice.lower() == 'r':
    #         print("Restarting...")
    #     else:
    #         print("Invalid choice. Please enter 'q' to quit or 'r' to restart.")