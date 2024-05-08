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

class App:
    def __init__(self, w=400, h=400, src_lang="", target_lang="", translator="Google") -> None:
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
        self.valqueue = Queue()

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
        print("Loading Detection & Recognition model EasyOCR...")
        self.detrec = TextDetectionRecognition(langchoice, use_gpu=True)

        if translator == "EasyNMT":
            print("Loading Translation model EasyNMT...")
            self.tl = EasyNMTranslator(
                self.lang_selected_src.get(),
                self.lang_selected_target.get()
            )
        elif translator == "Google":
            print("Loading Translation model GoogleTranslator...")
            self.tl = GoogleTranslator(
                self.lang_selected_src.get(),
                self.lang_selected_target.get()
            )
        print("Models loading completed!")
        print("Starting TexTranslator App...")

        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False
        self.capturemode = False
        self.pause = True
        self.inprocess = False
        self.starttime = 0

        self.placedlabel: list[tk.Canvas] = []
        self.labelcount = 0
        self.fontdict = [0 for _ in range(90)]
        self.fontsize_init()
        print(self.fontdict)

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
        self.starttime = time.time()
        self.screenbox.mainloop()

    def capture_toogle(self, event=None) -> None:
        self.pause = not self.pause
        color = "red" if self.pause else "green"
        self.machine_light.config(bg=color)

    def capture_screen_mss(self, event=None) -> None:
        if not self.valqueue.empty() and self.inprocess:
            try:
                boxtext = self.valqueue.get()
                print(boxtext[1])
                start = time.time()
                for x in range(len(boxtext[0])):
                    self.put_text_2(
                        x=int(boxtext[0][x][0][0]), 
                        y=int(boxtext[0][x][0][1]),
                        w=int(boxtext[0][x][2][0]-boxtext[0][x][0][0]),
                        h=int(boxtext[0][x][2][1]-boxtext[0][x][0][1]),
                        text=boxtext[1][x]
                    )
                print("Label placing time: ", time.time()-start)
                # self.put_text_2(
                #     x=int(boxtext[0][0][0]), 
                #     y=int(boxtext[0][0][1]),
                #     w=int(boxtext[0][2][0]-boxtext[0][0][0]),
                #     h=int(boxtext[0][2][1]-boxtext[0][0][1]),
                #     text=boxtext[1]
                # )
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
            
        self.screenbox.after(100, self.capture_screen_mss)

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
        ksize = (11,11)
        converted = cv2.blur(
            cv2.medianBlur(
                converted, 13, cv2.BORDER_REPLICATE
            ), ksize, cv2.BORDER_REPLICATE
        )
        # mask = np.zeros_like(cropped[:, :, 0])  # Create mask with same shape as first channel
        # mask[y:y+h, x:x+w] = 255  # Fill mask with white pixels for text region

        # # Apply inpainting with Telea algorithm
        # inpainter = cv2.ximgproc.createTeleaInpainting()
        # inpainter.setInpaintRadius(3)  # Adjust radius as needed
        # converted = inpainter.inpaint(cropped, mask, 3)

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
        self.machine_light.config(bg="red")
        self.inprocess = False

    def __det_textcolor(self, img):
        avglum = int(cv2.mean(
            cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:,:,2]
        )[0])
        return "#ffffff" if avglum <= 128 else "#000000"
    
    def __adjust_font_size(self, text:str, w:int, h:int) -> int:
        if not self.paragraphmode.get(): return self.fontdict[h]-3
        fontsize = int((h * (self.screenbox.winfo_height() * 1.25)) // self.dscreen_h)
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
    app = App(
        src_lang='ja', 
        target_lang='id', 
        translator="Google"
    )
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