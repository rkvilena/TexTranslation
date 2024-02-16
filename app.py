import pyautogui
import win32gui
import win32con
import win32api
import tkcap
import tkinter as tk
import cv2
import pygetwindow as gw
import numpy as np
from PIL import ImageGrab, ImageTk, Image

APP_NAME = "TexTranslation"
SCREENBOX_NAME = "Screenbox"

class App:
    def __init__(self, w=400, h=200) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.window_centered(self.root,w,h)

        self.screenbox = None
        self.root_sbox_btn = tk.Button(self.root, text = 'Open Screenbox', bd = '5', command = self.__open_screenbox)
        self.root_sbox_btn.pack(anchor=tk.CENTER)

        # Flags
        self.mode_deletemode = False
        self.screenbox_open = False

        # Create a canvas to display the captured image
        # Testing purpose, will be deleted
        self.canvas = tk.Canvas()
        self.canvas.pack()
        self.image = None
    
    def run(self) -> None:
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
        self.screenbox.bind("c", lambda event: self.capture_screen(event))

        self.screenbox_open = True

        self.put_text(0, 0, "SIUUU")
        self.put_text(100, 100, "SLEPET")

        self.screenbox.mainloop()

    def capture_screen(self, event=None):
        # Credit to 'tkcap' for the reference
        x, y = self.screenbox.winfo_x() + 8, self.screenbox.winfo_y() + 30
        w, h = self.screenbox.winfo_width(), self.screenbox.winfo_height() + 8
        ss = np.array(pyautogui.screenshot(region=(x, y, w, h)).convert('RGB'))
        self.image = cv2.cvtColor(ss, cv2.COLOR_RGB2BGR)  

        self.__display_image()

    def __display_image(self):
        # Convert the OpenCV image to Tkinter format
        # Test-purpose function
        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)))

        # Update the canvas with the new image
        self.canvas.config(width=img.width(), height=img.height())
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
        self.canvas.image = img

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
        self.screenbox.destroy()

    def window_centered(self, window, w, h) -> None:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()

        print(screen_w)
        print(screen_h)

        x = (screen_w - w) // 2
        y = (screen_h - h) // 2

        window.geometry(f"{w}x{h}+{x}+{y}")

    def print_test(self, event=None) -> None:
        # Modify as needed
        print("Print Executed!")

if __name__ == '__main__':
    app = App()
    app.run()