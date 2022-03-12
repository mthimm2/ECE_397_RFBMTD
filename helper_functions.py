# Static set of labels for use with detectnet
detectnet_label_set = set('person','bicycle','car','motorcycle','bus','train','truck')

# Takes in an image from the capture stream and returns the left and right edges of the three regions within that image
def segmentImage(img):

	x_seg = img.width / 3

	right  = (0, x_seg)
	center = (x_seg, x_seg*2)
	left   = (x_seg*2, x_seg*3)

	return right, center, left
	
# Determines which segment an object is in via the center of its bounding box
def determinePosition(img_center, right, center, left):

	# If x coord of center point is > left threshold of center segment and <= right threshold of center segment
	if img_center[0] >= center[0] and img_center[0] <= center[1]:
		return "center"
	# If x coord of center point is at or beyond the right-hand threshold of the center region 
	elif img_center[0] >= left[0]:
		return "left"
	# Otherwise, it's on the right
	else: # img_center <= right[1]:
		return "right"	

# Checks if the frame buffer is full, based on our specified FPS and time window
def is_frame_buffer_full(frames_queue, window, fps):

	# Check if the frame buffer is full
	return len(frames_queue) > window * fps

# Puts detected objects into their correct, spatial lists
def gather_detection_info(detections):

	# Objects go into one of these lists, based on location in the frame
	detection_left, detection_center, detection_right = [], [], []

	# Iterate through the detections
	for detection in detections:
		if detection.ClassID in detectnet_label_set:
			# We're only interested in the widths and center of the bounding box of each detected object
			info_tuple = (detection.Width, detection.Center)
			# LRC determination using the center coordinate of the 
			position = determinePosition(info_tuple[1])
			# Append to correct list
			if position == 'left':
				detection_left.append(info_tuple)
			elif position == 'center':
				detection_center.append(info_tuple)
			else:
				detection_right.append(info_tuple)

	# Return the completed lists
	return detection_left, detection_center, detection_right

# Based on all of the detections and their widths, we determine the closes object.
def determine_closest_object_per_segement(detection_left, detection_center, detection_right, width):

	# Refresh the variables to 0
	left_max_width, center_max_width, right_max_width, l_coeff, r_coeff, c_coeff = 0, 0, 0, 0, 0, 0
	
	# Take maximum width detection from each segment
	if len(detection_left) > 0:
		left_max_width = max([widths[0] for widths in detection_left])
		l_coeff = (left_max_width / width)# * distance_coeff
	if len(detection_center) > 0:
		center_max_width = max([widths[0] for widths in detection_center])
		c_coeff = (center_max_width / width)# * distance_coeff
	if len(detection_right) > 0:
		right_max_width = max([widths[0] for widths in detection_right])
		r_coeff = (right_max_width / width)# * distance_coeff

	# Return the updated variables
	return l_coeff, r_coeff, c_coeff