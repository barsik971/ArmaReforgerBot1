import pyautogui
import time

def hold_key(key, duration):
    pyautogui.keyDown(key)
    time.sleep(duration)
    pyautogui.keyUp(key)

def press_sequence(*keys, interval=0.1):
    for key in keys:
        pyautogui.press(key)
        time.sleep(interval)