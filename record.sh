#!/bin/bash

DISK_PERCENT_THRESHOLD=85
FILE_EXT=".h264"
SAVE_PATH="/home/pi/Videos/piDashcam/"
VIDEO_LEN=30000 #The time in ms of each recording

#Check to make sure we don't fill up the disk
echo "Max disk usage set to $DISK_PERCENT_THRESHOLD"
echo "Checking available disk space..."
diskUsage="$(df --output=pcent / | tr -dc '0-9')"
echo "${diskUsage} percent free."

if [[ $diskUsage -gt DISK_PERCENT_THRESHOLD ]]
then
	echo "Disk usage over ${DISK_PERCENT_THRESHOLD}."
	echo "Oldest files will be deleted."
fi

if [[ ! -e $SAVE_PATH ]]; then
		echo "Save directory does not exist. Creating new new directory..."
		mkdir $SAVE_PATH
	elif [[ ! -d $SAVE_PATH ]]; then
		echo "$dir already exists but is not a directory" 1>&2
fi

cd $SAVE_PATH

#Begin loop to record videos
while true
do
	now="$(date +"%Y_%m_%d_%I_%M_%S_%p")"
	newFileName="$now$FILE_EXT"

	if [[ $diskUsage -gt DISK_PERCENT_THRESHOLD ]]
	then
		oldestFileName="$(ls -1t | tail -1)"
		echo "Deleting $oldestFileName to make space for $newFileName"
		rm $oldestFileName
		
		#No old files exist. Thus need to manually free space or change DISK_PERCENT_THRESHOLD
		if [[ -z $oldestFileName ]]
		then
			echo "ERROR: No files to delete to make space. Adjust DISK_PERCENT_THRESHOLD or delete unneeded files."
			echo "Exiting."
			break
		fi
	fi
			
	echo "Starting recording of $newFileName ..."

	raspivid -t 30000 -w 1920 -h 1080 -o "$newFileName"
	echo "Recording saved to $SAVE_PATH$newFileName"
done
