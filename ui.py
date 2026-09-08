from tkinter import * # type: ignore
from tkinter import ttk
from tkinter import font

import subprocess
import threading

process: subprocess.Popen | None = None

def run_main_async():
    global process
    toggle_err.config(state="disabled")
    start_script.config(state="disabled")
    stop_script.config(state="normal")

    if process is None or process.poll() is not None:
        def worker():
            global process
            process = subprocess.Popen(["python", "mathspace.py", err_enabled.get()])
            process.wait()

            toggle_err.config(state="normal")
            start_script.config(state="normal")
            stop_script.config(state="disabled")

        threading.Thread(target=worker, daemon=True).start()

def murder():
    global process
    if process and process.poll() is None:
        process.kill()

def closed():
    murder()
    root.destroy()

root = Tk()
root.title("mathspacecheater")

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

font.nametofont("TkHeadingFont").config(weight="bold", size=12)

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=NSEW, padx=25, pady=25)

ttk.Label(mainframe, text="mathspacecheater", font="TkHeadingFont").grid(column=1, row=1, sticky=W, padx=(0, 10), pady=(0, 10))

open_chrome = ttk.Button(mainframe, text="Open Google Chrome", 
                         command=lambda: subprocess.run(["python", "openchrome.py"]))
open_chrome.grid(column=1, row=2, sticky=W, ipadx=4)

button_frames = ttk.Frame(mainframe)
button_frames.grid(column=1, row=3, sticky=W)

start_script = ttk.Button(button_frames, text="Start script", command=run_main_async)
start_script.grid(column=1, row=1, sticky=W)

stop_script = ttk.Button(button_frames, text="Stop script", command=murder, state="disabled")
stop_script.grid(column=2, row=1, sticky=W)

err_enabled = StringVar()
toggle_err = ttk.Checkbutton(mainframe, text="Skip errors?", variable=err_enabled, onvalue="False", offvalue="True")
toggle_err.grid(column=1, row=4, sticky=W)

root.minsize(280, 156)
root.resizable(False, False)

root.protocol("WM_DELETE_WINDOW", closed)
root.mainloop()