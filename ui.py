from tkinter import * # type: ignore
from tkinter import ttk
from tkinter import font

import subprocess
import threading

import signal
import sys
import os

import time

import json

chrome_path = R'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selene_profile"'

default_settings = {
    "api_key": "",
    "err_disabled": True,
    "get_from_env": False
}

pinned = False
settings = {}
debug_output = None

process: subprocess.Popen | None = None

def run_main_async():
    global process
    toggle_err.config(state="disabled")
    start_script.config(state="disabled")
    stop_script.config(state="normal")

    if process and process.poll() is None: return
    if get_from_env.get():
        key = ""
    else:
        key = api_key.get()
    
    if getattr(sys, 'frozen', False):
        file = ["mathspace.exe"]
    else:
        file = [sys.executable, "-u", "mathspace.py"]

    def read_output(pipe):
        while outputting:
            for bytes_line in iter(pipe.readline, b''):
                bytes_line: bytes
                line = bytes_line.decode('utf-8', "ignore")

                if debug_output is None: return
                debug_output.config(state="normal")
                debug_output.insert("end -2 chars", line + "\n")
                debug_output.config(state="disabled")

            time.sleep(0)

    def worker():
        global process
        global outputting

        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        process = subprocess.Popen(file + [str(err_disabled.get()), key], 
                                creationflags=creation_flags, stdout=subprocess.PIPE)

        outputting = True
        threading.Thread(target=read_output, args=(process.stdout,), daemon=True).start()
        process.wait()
        outputting = False

        toggle_err.config(state="normal")
        start_script.config(state="normal")
        stop_script.config(state="disabled")

    threading.Thread(target=worker, daemon=True).start()

def murder():
    global process

    if process is None or process.poll() is not None: return
    if sys.platform == "win32":
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.send_signal(signal.SIGINT)

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
    global debug_output

    def clear():
        if debug_output is None: return
        debug_output.config(state="normal")
        debug_output.delete(1.0, "end")
        debug_output.config(state="disabled")

    window = Toplevel(root)
    window.title("Debug")

    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    mainframe = ttk.Frame(window)
    mainframe.grid(column=0, row=0, sticky=NSEW, padx=25, pady=25)

    mainframe.columnconfigure(1, weight=1)
    mainframe.rowconfigure(2, weight=1)

    ttk.Label(mainframe, text="Output").grid(column=1, row=1, sticky=W)
    ttk.Button(mainframe, text="Clear", command=clear).grid(column=2, row=1, sticky=W)
    debug_output = Text(mainframe, state="disabled", height=0, width=0, font=("Cascadia Mono", 8))
    debug_output.grid(column=1, row=2, columnspan=2, sticky=NSEW)

    window.minsize(600, 400)

def pin():
    global pinned
    if pinned:
        root.attributes('-topmost', False)
        menubar.entryconfigure(3, label="📌")
    else:
        root.attributes('-topmost', True)
        menubar.entryconfigure(3, label="📍")

    pinned = not pinned

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
menubar.add_command(label="                                          ", state="disabled")
menubar.add_command(label="📌", command=pin)

mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=NSEW, padx=25, pady=25)

ttk.Label(mainframe, text="mathspacecheater", font="TkHeadingFont").grid(column=1, row=1, sticky=W, padx=(0, 10), pady=(0, 10))

open_chrome = ttk.Button(mainframe, text="Open Google Chrome", 
                         command=lambda: subprocess.Popen(chrome_path, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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