# installplaywrightbrowser.py
import subprocess
import sys

def install_playwright_browsers():
    subprocess.check_call([sys.executable, '-m', 'playwright', 'install'])

if __name__ == "__main__":
    install_playwright_browsers()
