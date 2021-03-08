#This dashcam script is a modified version of https://github.com/bnbe-club/rpi-dashcam-v1-diy-e38/blob/master/diy-e38/dashcam.py
#designed to work with the pijuice UPS hat


import picamera
import os
import sys
import psutil
import serial
import time
import datetime
import json
import itertools
import datetime as dt
import RPi.GPIO as GPIO

from picamera import Color
from pijuice import PiJuice # Import pijuice module
from subprocess import call

pijuice = PiJuice(1, 0x14) # Instantiate PiJuice interface object

DURATION = 30
SHUTDOWN_DELAY = 10
FINAL_DELAY = 5

SPACE_LIMIT = 85
MAX_FILES = 65000
MAX_TO_DELETE = 3

FPS = 30

AC_ON = "PRESENT"
NO_AC = "NOT_PRESENT"

folder_root = "/home/pi/"
videos_folder = "videos/"
path = folder_root + videos_folder
num_files = 0

def get_dir_files(path):
	os.chdir(path)
	return sorted(os.listdir(os.getcwd()), key=os.path.getmtime)

def get_disk_usage():
	return psutil.disk_usage("/").percent

def check_space():
	if(get_disk_usage() > SPACE_LIMIT):
		clear_space()
		
def clear_space():
	print('Attempting to free disk space...')
	attempts = 0
	num_deleted = 0
	while(get_disk_usage() > SPACE_LIMIT):
		attempts += 1
		if (attempts > MAX_TO_DELETE):
			print('Delete threshold reached. Disk space must be freed manually.')
			print('Exiting.')
			sys.exit()
			
		files = get_dir_files(path)		
		
		if (len(files) < 1):
			print('No existing videos to delete. Disk space must be freed manually.')
			print('Exiting.')
			sys.exit()
		else:
			oldest_file = files[0]
			print ('Deleting: ' + oldest_file)
			os.remove(oldest_file)
			
			num_deleted = num_deleted + 1

	print("Removed %d file(s)" % num_deleted)
	print('Completed.')

		
def shutdown_pi(delay):
	while(delay > 0):
		print("Shutting down in %d seconds" % delay, end="\r", flush=True)
		time.sleep(1)
		delay -= 1
	
	pijuice.rtcAlarm.SetWakeupEnabled(True)
	pijuice.power.SetWakeUpOnCharge(0)
	os.system("sudo shutdown -h now")
	#sys.exit()
	

def start_pi_dashcam():
	print('Starting pi dashcam')
	print('%d percent free disk space.' % (100 - get_disk_usage()))
	print('Save destination set to: %s' % path)
	
	if not os.path.exists(path):
		os.makedirs(path)
		print ('Created videos folder.')
		
	num_files = len(get_dir_files(path))
	print('Existing videos: %d' % num_files)

	check_space()

	with picamera.PiCamera() as camera:
		camera.resolution = (1920,1080)
		camera.framerate = FPS
		camera.start_preview()
		
		ac_disconnected = False
		shutdown_time = None
		
		while num_files < MAX_FILES:
			num_files += 1
			
			now = datetime.datetime.now()
			timestamp = "%d-%d-%d_%d_%d_%d" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
			
			file_name = path + "%s.h264" % timestamp

			print('Recording to %s' % file_name, end="\r", flush=True)
			timeout = time.time() + DURATION

			camera.start_recording(file_name, quality = 20)
			while(time.time() < timeout):

				camera.annotate_background = Color('black')
				camera.annotate_text = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

				check_space()
				power_status = pijuice.status.GetStatus()['data']['powerInput']

				if(power_status == NO_AC):
					if(ac_disconnected == False):
						ac_disconnected = True
						now = datetime.datetime.now()
						shutdown_time = now + datetime.timedelta(seconds = 10)
						print('Power disconnected! Automatic shutdown in %d seconds' % (SHUTDOWN_DELAY + FINAL_DELAY), end="\n")
					elif(datetime.datetime.now() >= shutdown_time):
						camera.stop_recording()
						camera.stop_preview()
						
						shutdown_pi(FINAL_DELAY)
				#elif(power_status == AC_ON and ac_disconnected == True):
				#	print('Power restored! Shutdown cancelled.')
				#	ac_disconnected = False
				#	shutdown_delay = 120 #reset the shutdown delay on power restore
					
				time.sleep(0.02)
			camera.stop_recording()

start_pi_dashcam()
