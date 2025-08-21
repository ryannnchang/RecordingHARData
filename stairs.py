from lsm6ds3 import LSM6DS3
import time
import RPi.GPIO as GPIO
import datetime
import csv
import qwiic_oled
import threading
import queue
import os

# ---------- helpers ----------
def read_acc(sent=0.000061):
    ax, ay, az, gx, gy, gz = lsm.get_readings()
    return ax*sent, ay*sent, az*sent

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def write_to_csv(filename, file_dict, data):
    file_folder = "data"
    file_path = f"{file_folder}/{file_dict}/{filename}.csv"
    ensure_dir(os.path.dirname(file_path))
    with open(file_path, 'a', newline='') as f:
        csv.writer(f).writerow(data)

def display(word):
    myOLED.clear(myOLED.PAGE)
    myOLED.set_cursor(0, 0)
    myOLED.print(word)
    myOLED.display()

def off():
    myOLED.clear(myOLED.ALL)
    myOLED.display()

# ---------- OLED ----------
myOLED = qwiic_oled.QwiicMicroOled()
myOLED.begin()
off()

# ---------- button / events ----------
BUTTON_PIN = 17
DEBOUNCE_S = 0.05
DOUBLE_WINDOW_S = 0.35

events = queue.Queue()              # "single" | "double"
recording_on = threading.Event()    # set => record loop runs

# Activity label that double-click toggles
label_options = ["walkingup", "walkingdown"]
label_index = 0
current_label = label_options[label_index]
label_lock = threading.Lock()

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def button_worker():
    setup_gpio()
    print("button_worker started")
    last_state = GPIO.input(BUTTON_PIN)  # True = HIGH (idle), False = LOW (pressed)
    last_fall_time = 0.0
    waiting_for_second = False

    while True:
        curr = GPIO.input(BUTTON_PIN)

        if last_state and not curr:  # falling edge
            t = time.time()
            time.sleep(DEBOUNCE_S)
            if GPIO.input(BUTTON_PIN):
                last_state = GPIO.input(BUTTON_PIN)
                continue

            if waiting_for_second and (t - last_fall_time) <= DOUBLE_WINDOW_S:
                waiting_for_second = False
                last_fall_time = 0.0
                events.put("double")
            else:
                waiting_for_second = True
                last_fall_time = t

        if waiting_for_second and (time.time() - last_fall_time) > DOUBLE_WINDOW_S:
            waiting_for_second = False
            last_fall_time = 0.0
            events.put("single")

        last_state = curr
        time.sleep(0.005)

def main_worker():
    print("main_worker started")
    global label_index, current_label

    while True:
        kind = events.get()
        if kind == "single":
            if recording_on.is_set():
                recording_on.clear()
                display("OFF")
                print("Recording stopped")
            else:
                recording_on.set()
                with label_lock:
                    lbl = current_label
                display(f"REC: {lbl}")
                print(f"Recording started ({lbl})")

        elif kind == "double":
            # Toggle between "walkingup" and "walkingdown"
            with label_lock:
                label_index = 1 - label_index
                current_label = label_options[label_index]
                lbl = current_label

            # Update display; if currently recording, show the new label
            if recording_on.is_set():
                display(f"REC: {lbl}")
            else:
                display(f"Label: {lbl}")
            print(f"Label changed to: {lbl}")

def recording_worker():
    print("recording_worker started")
    filename_down = "dw_ML1"
    filename_up = "up_ML1"
    file_dict_down = "walkingdown"
    file_dict_up = "walkingup" # keep your folder as 'walking' unless you want to split by label
    period = 0.02  # 50 Hz

    while True:
        if not recording_on.is_set():
            time.sleep(0.05)
            continue

        t0 = time.time()
        ax, ay, az = read_acc()
        date = datetime.datetime.now().isoformat()
        with label_lock:
            lbl = current_label
        # Replace 'test' with the current label
        if lbl == 'walkingup': 
            write_to_csv(filename_up, file_dict_up, [date, ax, ay, az, lbl])
        if lbl == 'walkingdown':
            write_to_csv(filename_down, file_dict_down, [date, ax, ay, az, lbl])

        elapsed = time.time() - t0
        time.sleep(max(0.0, period - elapsed))

if __name__ == "__main__":
    try:
        lsm = LSM6DS3()

        t1 = threading.Thread(target=button_worker, daemon=True)
        t2 = threading.Thread(target=main_worker, daemon=True)
        t3 = threading.Thread(target=recording_worker, daemon=True)

        t1.start(); t2.start(); t3.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        off()









  
  
  
  







