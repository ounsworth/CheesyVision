#!/usr/bin/env python
# Copyright (c) 2014, Team 254
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
#       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#       ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#       WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#       DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#       ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#       (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#       ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#       (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#       SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#       The views and conclusions contained in the software and documentation are those
#       of the authors and should not be interpreted as representing official policies,
#       either expressed or implied, of the FreeBSD Project.

# ~~~~~~~~~~~~~~~~~~~~
# ~~~ CheesyVision ~~~
# ~~~~~~~~~~~~~~~~~~~~
#
# This Python script uses your laptop's webcam and OpenCV to allow an operator to
# signal which goal is hot during autonomous mode.  You can think of it as a poor
# man's Kinect, but one that does not need a USB port, power supply, or special
# hardware.
#
# Configure the script by following the instructions posted here:
# https://github.com/Team254/CheesyVision
#
# Then, set your team number below and you are good to go!
#
# To use, run the script and see that there are three boxes overlayed on the webcam
# image.  The top center box is for "calibration", and it constantly computes the
# average color inside of the box as a reference.  The other two boxes are used for
# signalling the hot goal.  Basically, if the left and right boxes are about the same
# color as the calibration box, we assume the goal is hot.  If the color is different,
# we assume the goal is not hot.  If you are wearing a colorful, solid shirt, you can
# just use your hands - watch how the widget indicates what it sees as you move your
# hands through the boxes.  Or, you might find that a brightly colored object that your
# operator holds works better for you.  Before the match starts, hold up your hands, and
# then drop the one that corresponds to the hot goal.  The information is then sent to
# the cRIO.
#
# (We found that the "default hot" strategy works best, because it forces you to double
#  check that the camera is working before the match.)
#
# There are 5 keys that you can use to tweak the performance of the app:
#  1. Escape quits.
#  2. W and S increment and decrement exposure (if your webcam supports this feature).
#     This is very useful if you find the image looks too washed out.
#  3. A and D increment and decrement the color threshold used to tell if the color is
#     different.
#
# Enjoy!
import numpy as np
import cv, cv2

# CHANGE THIS TO BE YOUR TEAM'S cRIO IP ADDRESS!
HOST, PORT = "10.2.54.2", 1180

# Name of displayed window
WINDOW_NAME = "Visual Joystick"

# Width of the entire widget
WIDTH_PX = 1000

# Dimensions of the webcam image (it will be resized to this size)
WEBCAM_WIDTH_PX = 640
WEBCAM_HEIGHT_PX = 480

# This is the rate at which we will send updates to the cRIO.
UPDATE_RATE_HZ = 40.0
PERIOD = (1.0 / UPDATE_RATE_HZ) * 1000.0

paramsFile = 'params.yaml'

# pixel centres for the 4 buttons
btn1Ctr = (77, 415)
btn2Ctr = (217, 415)
btn3Ctr = (415, 415)
btn4Ctr = (558, 415)
btnRadiusSq = 40*40

def get_time_millis():
    ''' Get the current time in milliseconds. '''
    return int(round(time.time() * 1000))

minS = 40
maxS = 255
minV = 40
maxV = 255
minSize = 0.001
def detect_joystick( img ) :
	# convert image to HSV space and threshold it
	#hsv = cv.CreateImage(cv.GetSize(img), img.depth, 3);
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	
	mask = cv.fromarray( cv2.inRange( hsv, cv.Scalar(joystick_minH, minS, minV), cv.Scalar(joystick_maxH, maxS, maxV) ) )
	
	cv.Smooth( mask, mask, cv.CV_MEDIAN, 2*joystick_noiseFilterSize+1);
	
	cv2.imshow("Calibrate Joystick", np.array(mask) )
	
	w,h = cv.GetSize(mask)
	ys = np.array( range( h ) )
	ys = np.tile( np.array( range(h) ), ( w, 1) ).transpose()
	
	xs = np.array( range( w ) )
	xs = np.tile( np.array( range(w) ), ( h, 1) )
	
	npMask = np.array(mask).astype(float) / 255
	
	sum = np.sum(npMask)
	if (sum / (w*h) < minSize) :
		return -1, -1
		
	meanX = int( np.sum( xs * npMask ) / sum )
	meanY = int( np.sum( ys * npMask ) / sum )
	
	return meanX, meanY
	
def detect( img, minH, maxH, noiseFilterSize, windowName ) :
	# convert image to HSV space and threshold it
	#hsv = cv.CreateImage(cv.GetSize(img), img.depth, 3);
	hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	
	mask = cv.fromarray( cv2.inRange( hsv, cv.Scalar(minH, minS, minV), cv.Scalar(maxH, maxS, maxV) ) )
	
	cv.Smooth( mask, mask, cv.CV_MEDIAN, 2*noiseFilterSize+1);
	
	cv2.imshow(windowName, np.array(mask) )
	
	w,h = cv.GetSize(mask)
	ys = np.array( range( h ) )
	ys = np.tile( np.array( range(h) ), ( w, 1) ).transpose()
	
	xs = np.array( range( w ) )
	xs = np.tile( np.array( range(w) ), ( h, 1) )
	
	npMask = np.array(mask).astype(float) / 255
	
	sum = np.sum(npMask)
	if (sum / (w*h) < minSize) :
		return -1, -1
		
	meanX = int( np.sum( xs * npMask ) / sum )
	meanY = int( np.sum( ys * npMask ) / sum )
	
	return meanX, meanY
	
def writeParams( args) :
	'''Save the parameters to YAML file so they persist between runs. This is icing if I have time / energy'''
	global joystick_minH, joystick_maxH, joystick_noiseFilterSize
	global button_minH, button_maxH, button_noiseFilterSize
	
	joystick_minH = cv2.getTrackbarPos("joystick_minH", "Calibrate Joystick")
	joystick_maxH = cv2.getTrackbarPos("joystick_maxH", "Calibrate Joystick")
	joystick_noiseFilterSize = cv2.getTrackbarPos("joystick size of noise filter", "Calibrate Joystick")
	
	button_minH = cv2.getTrackbarPos( "button_minH", "Calibrate Button")
	button_maxH = cv2.getTrackbarPos( "button_maxH", "Calibrate Button")
	button_noiseFilterSize = cv2.getTrackbarPos( "button size of noise filter", "Calibrate Button")
	
	
	params = {}
	params["joystick_minH"] = joystick_minH
	params["joystick_maxH"] = joystick_maxH
	params["joystick_noiseFilterSize"] = joystick_noiseFilterSize
	params["button_minH"] = button_minH
	params["button_maxH"] = button_maxH
	params["button_noiseFilterSize"] = button_noiseFilterSize
	
	# convert this to YAML format
	YAMLstr = yaml.dump( params )
	
	# save it to a file
	file = open(paramsFile, 'w')
	file.write(YAMLstr)
	file.close()
	
def readParams() :
	global joystick_minH, joystick_maxH, joystick_noiseFilterSize
	global button_minH, button_maxH, button_noiseFilterSize
	
	try :
		file = open(paramsFile, 'r')
	except IOError:
		# file not there, use the default parameters
		return
		
	input = file.read()
	file.close()
	
	# convert the raw text into a dictionary
	params = yaml.load( input )
	
	# extract the individual variables
	try :
		joystick_minH = params["joystick_minH"]
		joystick_maxH = params["joystick_maxH"]
		joystick_noiseFilterSize = params["joystick_noiseFilterSize"]
		button_minH = params["button_minH"]
		button_maxH = params["button_maxH"]
		button_noiseFilterSize = params["button_noiseFilterSize"]
	except KeyError as e :
		# the file was corrupt, go with the default values
		print("File Corrupt")
		return

joyColour = (0, 255, 0)
btnColour = (255, 0, 0)
alpha = 0.6 # for the smoothing to reduce jitter
def main():
	global joystick_minH, joystick_maxH, joystick_noiseFilterSize
	global button_minH, button_maxH, button_noiseFilterSize
	cv.NamedWindow(WINDOW_NAME, 1)
    
    # TODO : team number entry box
    
	joystick_minH = joystick_maxH = joystick_noiseFilterSize = 0
	button_minH = button_maxH = button_noiseFilterSize = 0
	readParams()
	
	cv.NamedWindow("Calibrate Joystick", 1)
	cv.CreateTrackbar( "joystick_minH", "Calibrate Joystick", joystick_minH, 255, writeParams)
	cv.CreateTrackbar( "joystick_maxH", "Calibrate Joystick", joystick_maxH, 255, writeParams)
	cv.CreateTrackbar( "joystick size of noise filter", "Calibrate Joystick", joystick_noiseFilterSize, 25, writeParams)
	#cv.WaitKey(5);
    
	cv.NamedWindow("Calibrate Button", 1)
	cv.CreateTrackbar( "button_minH", "Calibrate Button", button_minH, 255, writeParams)
	cv.CreateTrackbar( "button_maxH", "Calibrate Button", button_maxH, 255, writeParams)
	cv.CreateTrackbar( "button size of noise filter", "Calibrate Button", button_noiseFilterSize, 25, writeParams)
	cv.WaitKey(5);

	# Open the webcam (should be the only video capture device present).
	capture = cv2.VideoCapture(0)

	# Manually set the exposure, because a lot of webcam drivers will overexpose
	# the image and lead to poor separation between foreground and background.
	#exposure = -4
	#last_exposure = exposure
	#capture.set(15, exposure)  # 15 is the enum value for CV_CAP_PROP_EXPOSURE

	# Keep track of time so that we can provide the cRIO with a relatively constant
	# flow of data.
	last_t = get_time_millis()

	# Are we connected to the server on the robot?
	connected = False
	s = None

	oldJoyX = oldJoyY = oldBtnX = oldBtnY  = 0
	while 1:
		# Get a new frame.
		_, img = capture.read()

		# Flip it and shrink it.
		img = cv2.flip(cv2.resize(img, (WEBCAM_WIDTH_PX, WEBCAM_HEIGHT_PX)), 1)

		#joyX, joyY = detect_joystick( img )
		joyX, joyY = detect( img, joystick_minH, joystick_maxH, joystick_noiseFilterSize, "Calibrate Joystick")
		btnX, btnY = detect( img, button_minH, button_maxH, button_noiseFilterSize, "Calibrate Button")
		
		if (joyX != -1 and joyY != -1) :
			joyX = int( alpha*joyX + (1-alpha)*oldJoyX )
			joyY = int( alpha*joyY + (1-alpha)*oldJoyY )
			oldJoyX = joyX
			oldJoyY = joyY
						
			cv2.circle( img, (joyX, joyY), 15, joyColour, thickness=-1 )
		
		overlayFile = 'axes.png'
		if (btnX != -1 and btnY != -1) :
			btnX = int( alpha*btnX + (1-alpha)*oldBtnX )
			btnY = int( alpha*btnY + (1-alpha)*oldBtnY )
			oldBtnX = btnX
			oldBtnY = btnY
						
			cv2.circle( img, (btnX, btnY), 15, btnColour, thickness=-1 )
			
			# is this within any of the button circles?
			distSqBtn1 = (btnX - btn1Ctr[0])*(btnX - btn1Ctr[0]) + (btnY - btn1Ctr[1])*(btnY - btn1Ctr[1])
			distSqBtn2 = (btnX - btn2Ctr[0])*(btnX - btn2Ctr[0]) + (btnY - btn2Ctr[1])*(btnY - btn2Ctr[1])
			distSqBtn3 = (btnX - btn3Ctr[0])*(btnX - btn3Ctr[0]) + (btnY - btn3Ctr[1])*(btnY - btn3Ctr[1])
			distSqBtn4 = (btnX - btn4Ctr[0])*(btnX - btn4Ctr[0]) + (btnY - btn4Ctr[1])*(btnY - btn4Ctr[1])
			
			if( distSqBtn1 < btnRadiusSq ) :
				overlayFile = 'axesB1.png'
				btnPressed = 1
			elif( distSqBtn2 < btnRadiusSq ) :
				overlayFile = 'axesB2.png'
				btnPressed = 2
			elif( distSqBtn3 < btnRadiusSq ) :
				overlayFile = 'axesB3.png'
				btnPressed = 3
			elif( distSqBtn4 < btnRadiusSq ) :
				overlayFile = 'axesB4.png'
				btnPressed = 4
			else :
				overlayFile = 'axes.png'
				btnPressed = 0
			
		# overlay axes and some buttons
		overlay = cv2.imread(overlayFile)
		
		# detect which pixels in the overlay have something in them
		# and make a binary mask out of it
		overlayMask = cv2.cvtColor( overlay, cv2.COLOR_BGR2GRAY )
		res, overlayMask = cv2.threshold( overlayMask, 10, 1, cv2.THRESH_BINARY_INV)
		
		# expand the mask from 1-channel to 3-channel
		h,w = overlayMask.shape
		overlayMask = np.repeat( overlayMask, 3).reshape( (h,w,3) )
		
		# mask out the pixels that you want to overlay
		img *= overlayMask
		img += overlay
		
		# Show the image.
		cv2.imshow(WINDOW_NAME, img)
		
		
		
		# TODO: send axes and buttons to cRIO

		# Throttle the output
		#cur_time = get_time_millis()
		#if last_t + PERIOD <= cur_time:
			## Try to connect to the robot on open or disconnect
			#if not connected:
				#try:
					## Open a socket with the cRIO so that we can send the state of the hot goal.
					#s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

					## This is a pretty aggressive timeout...we want to reconnect automatically
					## if we are disconnected.
					#s.settimeout(.1)
					#s.connect((HOST, PORT))
				#except:
					#print "failed to reconnect"
					#last_t = cur_time + 1000
			#try:
				## Send one byte to the cRIO:
				## 0x01: Right on
				## 0x02: Left on
				## 0x03: Both on
				#write_bytes = bytearray()
				#v = (left_on << 1) | (right_on << 0)
				#write_bytes.append(v)
				#s.send(write_bytes)
				#last_t = cur_time
				#connected = True
			#except:
				#print "Could not send data to robot"
				#connected = False


		# Capture a keypress.
		key = cv.WaitKey(10) & 255

		# Escape key.
		if key == 27:
			break

	s.close()

if __name__ == '__main__':
    main()
