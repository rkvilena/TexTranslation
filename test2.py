import tkinter as tk
import win32gui
import win32con
import win32api

def set_transparent(window, transparency):
    hwnd = window.winfo_id()
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,
                       win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0, 0, 0), transparency, win32con.LWA_COLORKEY)

root = tk.Tk()
root.title("Transparent Tkinter Window")

# Set window size and position
root.geometry("400x300+100+100")

# Set transparency (0: fully transparent, 255: fully opaque)
transparency_level = 150
set_transparent(root, transparency_level)

# Add widgets or components to the transparent window
label = tk.Label(root, text="Transparent Window")
label.pack(padx=20, pady=20)

root.mainloop()