import subprocess

subprocess.Popen(r'"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\selene_profile"', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)