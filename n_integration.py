#!/usr/bin/python3
#
# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#

# Eric Moravek and Max Thimmig
# UIC Senior Design 3/2022
# Rear Facing Bicycle Mounted Vehicle Detection System. RF-VDS
# Version V1.0

import numpy as np
from bikecam import *
import jetson.inference
import jetson.utils
#import os
import argparse
import sys

# Parser Parameters
parser = argparse.ArgumentParser(description="Locate objects in a live camera stream using an object detection DNN.", 
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson.inference.detectNet.Usage() +
                                 jetson.utils.videoSource.Usage() + jetson.utils.videoOutput.Usage() + jetson.utils.logUsage())
parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="ssd-mobilenet-v2", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="box,labels,conf", help="detection overlay flags (e.g. --overlay=box,labels,conf)\nvalid combinations are:  'box', 'labels', 'conf', 'none'")
parser.add_argument("--threshold", type=float, default=0.5, help="minimum detection threshold to use") 
parser.add_argument("--snapshots", type=str, default="images/test/detections", help="output directory of detection snapshots")
parser.add_argument("--timestamp", type=str, default="%Y%m%d-%H%M%S-%f", help="timestamp format used in snapshot filenames")
#parser.add_argument("--labels", type=str, default="jetson-inference/Integration/ssd_bikedetectnet_labels.txt", help="Path to label text file, COCO Default all labels is:  \n jetson-inference/data/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt")

# Old Parser Command
# parser.add_argument("input_URI", type=str, default="", nargs='?', help="URI of the input stream")
# parser.add_argument("output_URI", type=str, default="", nargs='?', help="URI of the output stream")
# parser.add_argument("--network",type=str, default="ssd-mobilenet-v2", help="Choose the network to use. default: ssd-mobilenet-v2 \n Can use ssd-inception-v2, multiped,ssd-mobilenet-v1, ect")
# parser.add_argument("--labels",type=str, default="jetson-inference/BikeDetectNet/ssd_bikedetectnet_labels.txt", help="Path to label text file, COCO Default all labels is:  \n jetson-inference/data/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt")
# parser.add_argument("--overlay",type=str,default="box labels conf", help="detection overlay flags, Valid combinations are: 'box', 'labels' ,'conf', 'none'")
# parser.add_argument("--threshold", type=float,default=0.5, help="Choose the threshold parameter, Default: 0.5")
args = parser.parse_args()

is_headless = ["--headless"] if sys.argv[0].find('console.py') != -1 else [""]

# Print Help if error Parsing 
try:
	opt = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)


# create video output object and input object
input_stream = jetson.utils.videoSource(opt.input_URI, argv=sys.argv+['--input-flip=rotate-180'])
output_stream = jetson.utils.videoOutput(opt.output_URI, argv=sys.argv+is_headless)


# Use the custom labels to only detect: person, car, bus, truck, bicycle, motorcycle, unlabled, located in "jetson-inference/BikeDetectNet/ssd_bikedetectnet_labels.txt"
# load the detection network 
net = jetson.inference.detectNet(args.network, sys.argv, args.threshold)

# net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5) # Left over code delete if not needed.

# # create video sources 
# input = jetson.utils.videoSource(opt.input_URI, argv=sys.argv)


# Set up the Camera and Video output display.
#camera = jetson.utils.videoSource("csi://0")      # '/dev/video0' for V4L2
camera = jetson.utils.videoSource("csi://0", argv=['--input-flip=rotate-180', '--input-width=1280', '--input-height=720', '--input-frameRate=30'])
display = jetson.utils.videoOutput("display://0") # 'my_video.mp4' for file

#IMAGE_PATH = '/jetson-inference/Integration/max_sample_images'

# Instantiate the bike cam
bikecam = BikeCam(

	filename    = 'video',
    resolution  = '720p',
    vid_format  = "mp4",
    window      = 90,      # 300 sec = 5 mins (get last 5 mins)
    fps         = 15.0      # personal webcam = 15 fps

)

try:
	# While loop
	while True:

		# Capture an image from the camera.
		img = camera.Capture()

		# Moving Window frame management
		if time.time() - bikecam.start > bikecam.WINDOW:
		                
			if time.time() - bikecam.start == bikecam.WINDOW:
				print("Moving Window Activated")
				print(f"Window limit reached: {len(bikecam.frames_queue)}")

			# remove frames that are out of the time window 
			bikecam.frames_queue.pop(0)   # first in, first out

		#if KeyboardInterrupt:
			#bikecam.convertFrameToVideo()
			#print("Keyboard was stopped with interrupt")  

		#for image in os.listdir(IMAGE_PATH):

		# Convert jpegs to workable format
		#img = jetson.utils.loadImage(IMAGE_PATH + '/' + image)
		#img_cuda = jetson.utils.cudaAllocMapped(width=img.width, height = img.height, format = img.format)
		#jetson.utils.cudaMemcpy(img_cuda, img)

		# Detect the Objects in the image and store them in detections.
		detections = net.Detect(img, overlay=opt.overlay)

		# Convert BGR frame to RGB
		img_cuda = jetson.utils.cudaAllocMapped(width = img.width, height = img.height, format = 'bgr8')

		jetson.utils.cudaConvertColor(img, img_cuda)

		# print the detections
		print("detected {:d} objects in image".format(len(detections)))

		# Print out all the detections
		for detection in detections:
			print(detection)

		# Display the image and the objects detected and the preformance.
		#display.Render(img)

		display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
		
		# update the title bar
		output_stream.SetStatus("{:s} | Network {:.0f} FPS".format(opt.network, net.GetNetworkFPS()))

		# print out performance info
		#net.PrintProfilerTimes()

		# Can the gstream write out these images/frames captured by the jetson utilities?
		# Gotta figure out how to flip BRG -> RGB
		bikecam.frames_queue.append(np.array(img_cuda))

		# exit on input/output EOS
		# if not input.IsStreaming() or not output.IsStreaming():
		# 	break

finally:
	bikecam.convertFrameToVideo()

