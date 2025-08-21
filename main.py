from lsm6ds3 import LSM6DS3
import time
import RPi.GPIO as GPIO
import datetime
import csv
import qwiic_oled

def read_acc(sent=0.000061):
  ax, ay, az, gx, gy, gz = lsm.get_readings()
  ax = ax * sent
  ay = ay * sent
  az = az * sent

  return ax, ay, az

def write_to_csv(filename, file_dict, data):
  file_folder = "data"
  file_path = f"{file_folder}/{file_dict}/{filename}.csv"

  with open(file_path, 'a') as file:
    writer = csv.writer(file)
    writer.writerow([data[0], data[1], data[2], data[3], data[4]])

def display(word):
	myOLED.clear(myOLED.PAGE)
	myOLED.print(word)
	myOLED.set_cursor(0,0)
	myOLED.display()
  
def off():
  myOLED.clear(myOLED.ALL)



#Intialize screen
myOLED = qwiic_oled.QwiicMicroOled()
myOLED.begin()
myOLED.clear(myOLED.ALL)
myOLED.clear(myOLED.PAGE)



def main():
  # Ask for FileNames
  file_dict = str(input("Enter the motion: "))
  filename = str(input("Enter the filename: "))
  
  #Initialize GPIO
  global lsm
  lsm = LSM6DS3()

  # Initialize GPIO for button
  button = 17
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(button, GPIO.IN)
  
  #Button setup
  toggle_state = False
  last_state = GPIO.input(button)

  while True:
    current_state = GPIO.input(button)
    
    if last_state == True and current_state == False:
      toggle_state = not toggle_state
      if toggle_state == True:
        print("Recording...")
        display("Recording...")
      else:
        print("Off")
        display("Off")
      
    last_state = current_state
    
    if toggle_state == True:
      ax, ay, az = read_acc()
      date = datetime.datetime.now()
      data = [date, ax, ay, az, file_dict]
      time.sleep(0.02)
      
      write_to_csv(filename, file_dict, data)
    
main()
off()


