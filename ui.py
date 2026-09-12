from tkinter import * # type: ignore
from tkinter import ttk
from tkinter import font

import subprocess
import threading

import json

default_settings = {
    "api_key": "",
    "err_disabled": True,
    "get_from_env": False
}

settings = {}
process: subprocess.Popen | None = None

def run_main_async():
    global process
    toggle_err.config(state="disabled")
    start_script.config(state="disabled")
    stop_script.config(state="normal")

    if process is None or process.poll() is not None:
        if not get_from_env.get():
            key = api_key.get()
        else:
            key = ""

        def worker():
            global process
            process = subprocess.Popen(["python", "mathspace.py", str(err_disabled.get()), key])
            process.wait()

            toggle_err.config(state="normal")
            start_script.config(state="normal")
            stop_script.config(state="disabled")

        threading.Thread(target=worker, daemon=True).start()

def murder():
    global process
    if process and process.poll() is None:
        process.kill()

def settings_window():
    global get_from_env
    global api_key

    window = Toplevel(root)
    window.title("Settings")

    mainframe = ttk.Frame(window)
    mainframe.grid(column=0, row=0, sticky=NSEW, padx=25, pady=25)

    ttk.Label(mainframe, text="Settings", font="TkHeadingFont").grid(column=1, row=1, sticky=W, padx=(0, 10), pady=(0, 10))

    key_entry = ttk.Checkbutton(mainframe, text="Get API Key from enviroment variables", 
                                variable=get_from_env, onvalue=True, offvalue=False)
    key_entry.grid(column=1, row=2, columnspan=2, sticky=W)
    
    ttk.Label(mainframe, text="API Key (Gemini)").grid(column=1, row=3, sticky=W)

    ttk.Entry(mainframe, textvariable=api_key).grid(column=2, row=3, sticky=W)


def update_settings():
    settings.update({
        "get_from_env": get_from_env.get(),
        "api_key": api_key.get(),
        "err_disabled": err_disabled.get(),
    })

    json.dump(settings, open("settings.json", "w"), indent=4, sort_keys=True)

def debug_window():
    window = Toplevel(root)
    window.title("Debug")

    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    mainframe = ttk.Frame(window)
    mainframe.grid(column=0, row=0, sticky=NSEW, padx=25, pady=25)

    mainframe.columnconfigure(1, weight=1)
    mainframe.columnconfigure(2, weight=1)
    mainframe.rowconfigure(2, weight=3)
    mainframe.rowconfigure(4, weight=1)

    ttk.Label(mainframe, text="Input").grid(column=1, row=1, sticky=W)
    ttk.Entry(mainframe, state="readonly").grid(column=1, row=2, sticky=NSEW)

    ttk.Label(mainframe, text="Output").grid(column=1, row=3, sticky=W)
    ttk.Entry(mainframe, state="readonly").grid(column=1, row=4, sticky=NSEW)

    ttk.Label(mainframe, text="Errors").grid(column=2, row=1, sticky=W)
    ttk.Entry(mainframe, state="readonly").grid(column=2, row=2, rowspan=3, sticky=NSEW)

def closed():
    murder()
    update_settings()
    root.destroy()


root = Tk()
root.title("mathspacecheater")

font.nametofont("TkHeadingFont").config(weight="bold", size=12)

try:
    settings = json.load(open("settings.json", "r"))
except:
    settings = default_settings

get_from_env = BooleanVar(value=settings["get_from_env"])
api_key = StringVar(value=settings["api_key"])
err_disabled = BooleanVar(value=settings["err_disabled"])

root.option_add('*tearOff', FALSE)
menubar = Menu(root)
root["menu"] = menubar

menubar.add_command(label="Settings", command=settings_window)
menubar.add_command(label="Debug", command=debug_window)

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

toggle_err = ttk.Checkbutton(mainframe, text="Skip errors?", variable=err_disabled, onvalue=True, offvalue=False)
toggle_err.grid(column=1, row=4, sticky=W)

root.minsize(280, 156)
root.resizable(False, False)

root.protocol("WM_DELETE_WINDOW", closed)
root.mainloop()