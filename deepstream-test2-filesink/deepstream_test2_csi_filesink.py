#!/usr/bin/env python3

################################################################################
# SPDX-FileCopyrightText: Copyright (c) 2019-2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################



import sys
import os
from optparse import OptionParser
import time
#sys.path.append('../')
# Changed to absolute path
sys.path.append('/opt/nvidia/deepstream/deepstream-6.0/sources/deepstream_python_apps/apps')
import platform
import configparser

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
from gi.repository import GObject, Gst 
from gi.repository import GLib
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
import pyds
import subprocess
import signal


# Import Battery Module
from battery_module import *
import struct
import smbus

# # Import GPIO For Button Presses
import Jetson.GPIO as GPIO
print(GPIO.JETSON_INFO)
# Pin Definitions
input_pin = 15  # BCM pin 6, BOARD pin 31
# Connect 3.3v 4.7K to 10K Pull up resistor to input pin and connect button to input_pin and ground.
# Pin Setup:
GPIO.setmode(GPIO.BOARD)  # BCM pin-numbering scheme from Raspberry Pi
GPIO.setup(input_pin, GPIO.IN)  # set pin as an input pin
print("GPIO PIN(15): ", GPIO.input(input_pin))




# Import Uart Communication Module
from uart_module import *

# To Print The dot graph Gstreamer pipeline
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/home/team3/Documents/Pipeline_Config"
os.putenv('GST_DEBUG_DUMP_DIR_DIR', '/home/team3/Documents/Pipeline_Config')

# Program Parameters
RECORD_ON = True
input_file = None
no_display = False
PGIE_CONFIG_FILE = "dstest2_pgie_config2.txt"
TRACKER_CONFIG_FILE = 'dstest2_tracker_config2.txt'

# Class definition
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

# For Debug Print Onto display for data recording.
class_id_names = ["Car","Bicycle","Person","Roadsign","No bBox"]


# Global Declaration
loop = None
pipeline = None
streammux = None
bus = None

MAX_NUM_SOURCES = 1
g_num_sources = 0
g_source_id_list = [0] * MAX_NUM_SOURCES
g_eos_list = [False] * MAX_NUM_SOURCES
# g_source_enabled = [False] * MAX_NUM_SOURCES
# g_source_bin_list = [None] * MAX_NUM_SOURCES

# History dictionary for the past LCR detections
lcr_history = {}

# Constants for Location Determination
# We know that each frame coming in has the same dimensions for 720p capture
STANDARD_FRAME_WIDTH = 1280
STANDARD_FRAME_HEIGHT = 720

# This lets us statically define the LCR regions
# These numbers reflect that fact That we're looking behind us. Hence right is on the left of the frame.
RIGHT = (0, STANDARD_FRAME_WIDTH / 3)
CENTER = (STANDARD_FRAME_WIDTH / 3, 2 * (STANDARD_FRAME_WIDTH / 3))

# Constants that represent when a vehicle is close, medium, or far away.
# Meant to line up with the coefficients that we obtain from detection processing below.
CLOSE_WIDTH = 180
MED_WIDTH = 105
FAR_WIDTH = 40


# Turn on and off Functionality
battery_connected = True
serial_connected = True
gpio_connected = False


i = 0
# GPIO Interrupt Callback Test
def callback_fn(input_pin):
    global i
    i=i + 1
    print("Button Pressed: ", i)
    exit_call2()

# Add GPIO Interrupt
GPIO.add_event_detect(input_pin, GPIO.FALLING, callback=callback_fn, bouncetime=200)

if serial_connected:
    try:
        # Initialize UART_Jetson Object
        uart_transmission = UART_Jetson()
    
    except:
        print("Exception: Serial Not Connected")
        serial_connected = False

if battery_connected:
    try:
        # battery status (hold the last known battery level)
        bat_bus = smbus.SMBus(1)
        
    except:
        print("Exception: Battery Not Connected")
        battery_connected = False

previous_battery_state = ""

# Button Pressed Interupt
def button_pressed(channel):
    print("Button Pressed")



# osd_sink_pad_buffer_probe  will extract metadata received on OSD sink pad
# and update params for drawing rectangle, object information etc.
# IMPORTANT NOTE:
# a) probe() callbacks are synchronous and thus holds the buffer
#    (info.get_buffer()) from traversing the pipeline until user return.
# b) loops inside probe() callback could be costly in python.
#    So users shall optimize according to their use-case.
def osd_sink_pad_buffer_probe(pad,info,u_data):
    
    global pipeline
    global bus
    global loop

    global bat_busw
    global previous_battery_state
    global lcr_history

    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return
   
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))


    # Debug Default index for class name, Used for Printing out what object is detected on screen.
    #class_id_index = 4
    
    # Debug: Set info_tuple default value so if l_obj is None it will be defined when debug is displaying info_tuple name.
    #info_tuple = (0,0,0)
    

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        
        except StopIteration:
            break

        # Lists for objects detected in LRC regions
        left_det, center_det, right_det = [], [], []

        # Get list of the objects in frames' metadata
        l_obj=frame_meta.obj_meta_list

        obj_meta = None


        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                #obj_meta=pyds.glist_get_nvds_object_meta(l_obj.data)
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)


            except StopIteration:
                break

            object_id = str(obj_meta.object_id)
            # print("object_id: ", object_id)

            # Debug for on screen display of class name 
            #class_id_index = obj_meta.class_id
            
            #obj_meta.rect_params.border_color.set(0.0, 0.0, 1.0, 0.0)
            
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break

            # Dive through casts to get the object's bounding box top left vertex, width, and height?
            #obj_bb_coords = pyds.NvBbox_Coords.cast(pyds.NvDsComp_BboxInfo.cast(obj_meta.tracker_bbox_info))

            obj_bb_coords = obj_meta.tracker_bbox_info.org_bbox_coords
            # print("obj_bb_coords: ", obj_bb_coords.top, " \n")

            # Used to determine whether or not an object is approaching or receding in frame
            obj_bb_area = obj_bb_coords.height * obj_bb_coords.width

            # Construct the bounding box for this object. tvl top left vertex, brv: bottom right vertex
            obj_tlv = (obj_bb_coords.left, obj_bb_coords.top)
            obj_brv = (obj_bb_coords.left + obj_bb_coords.width, obj_bb_coords.top + obj_bb_coords.height)
            obj_center_coords = ((obj_tlv[0] + obj_brv[0]) / 2, (obj_tlv[1] + obj_brv[1]) / 2)

            # For the purpose of object distance calculation and position, we care mostly about bb width and bb center location
            info_tuple = (obj_bb_coords.width, obj_center_coords, obj_bb_area, obj_meta.object_id)
            
            detection_object_class = 0 # 0: car, 2: person

            # print("LCR History: ", lcr_history)
            # Initialize the object and insert it into the history dictionary if not already provided : 0 is for car and 2 is for person
            if obj_meta.object_id not in lcr_history and obj_meta.class_id is detection_object_class: # TODO change 2 back to 0 to inference cars.
                lcr_history[obj_meta.object_id] = {}
                lcr_history[obj_meta.object_id]['delta_w'] = 0
                lcr_history[obj_meta.object_id]['delta_h'] = 0
                lcr_history[obj_meta.object_id]['direction'] = None
                lcr_history[obj_meta.object_id]['width'] = obj_bb_coords.width
                lcr_history[obj_meta.object_id]['height'] = obj_bb_coords.height
                lcr_history[obj_meta.object_id]['tlv'] = obj_tlv
                lcr_history[obj_meta.object_id]['brv'] = obj_brv
            
            # What dpes this elif do. Class Id for car is 0.
            elif obj_meta.class_id == detection_object_class:
                
                lcr_history[obj_meta.object_id]['delta_w'] = lcr_history[obj_meta.object_id]['width'] - obj_bb_coords.width
                lcr_history[obj_meta.object_id]['delta_h'] = lcr_history[obj_meta.object_id]['height'] - obj_bb_coords.height
                lcr_history[obj_meta.object_id]['direction'] = 'left' if obj_tlv[0] > lcr_history[obj_meta.object_id]['tlv'][0] else 'right' if obj_tlv[0] != lcr_history[obj_meta.object_id]['tlv'][0] else None
                lcr_history[obj_meta.object_id]['width'] = obj_bb_coords.width
                lcr_history[obj_meta.object_id]['height'] = obj_bb_coords.height
                lcr_history[obj_meta.object_id]['tlv'] = obj_tlv
                lcr_history[obj_meta.object_id]['brv'] = obj_brv

            # If an object is determined to be approaching us, we allow it to be placed into the...
            # Based on where the center of the bb of the object is, we classify it as being in either the L,C, or R segment of the frame  
            # if obj_meta.object_id in lcr_history and obj_meta.class_id is detection_object_class:
            if obj_meta.object_id in lcr_history:
                if lcr_history[obj_meta.object_id]['delta_w'] >= 0:
                    if obj_center_coords[0] < RIGHT[1]:
                        right_det.append(info_tuple)
                    elif obj_center_coords[0] >= CENTER[0] and obj_center_coords[0] < CENTER[1]:
                        center_det.append(info_tuple)
                    else:
                        left_det.append(info_tuple)

            # Clean out the history dictionary of all of the objects that were moving away.
            for key, value in lcr_history.copy().items() :
                if value['delta_w'] < 0:
                    lcr_history.pop(key)

        # Debug 
        location = 'None'
        left_data  = '0'
        center_data  = '0'
        right_data  = '0'
        # battery_data  = '00'
        serial_data_package = ''


        # Make sure that we actuall have an object to look at
        if obj_meta is not None:

            # Determine closes object in each frame
            l_max_width = max([info_tuple[0] for info_tuple in left_det])   if len(left_det)    > 0 else 0
            r_max_width = max([info_tuple[0] for info_tuple in right_det])  if len(right_det)   > 0 else 0
            c_max_width = max([info_tuple[0] for info_tuple in center_det]) if len(center_det)  > 0 else 0

            '''
                Do we need to have any special considerations for objects not in the center segment?
                Is this where we make use of the distance coefficient to help compensate for the fish-eyeing?
            '''
            # Ratio of bounding box width to width of the frame
            # Serves as a rudimentary form of how close an object is
            # l_coeff = l_max_width / STANDARD_FRAME_WIDTH
            # r_coeff = r_max_width / STANDARD_FRAME_WIDTH
            # c_coeff = c_max_width / STANDARD_FRAME_WIDTH

            # Dubug width list for data recording. 
            # width_list = [l_max_width,c_max_width,r_max_width]
            
            # Eric: for testing get the bounding box coeff for the given region
            coeff = [l_max_width, c_max_width, r_max_width]
            location_list = ['Left','Center','Right']
            max_coeff = max(coeff)
            max_index = coeff.index(max_coeff)
            location = location_list[max_index]     

            # Distance estimation function:
            # distance = c_coeff*var 

            '''
            -- Needs Updating
            FDU Code:
                L | C | R | S | B | Other Function
                0 | 1 | 2 | 3 | 4 |
                L, C, R  => 0, 1, 2, 3     [0=off, 1=close, 2=med, 3=far]
                S => 0, 1                  [0=off, 1=on]
                B => 0, 1, 2, 3, 4         [0=off, 1 : < 25, 2 : >25,  3 : >50, 4 : >75]
                Other Functions => TBD
            '''
            # Serial Data Preprocessing
            print("L_max_width: ", l_max_width)
            print("C_max_width: ", c_max_width)
            print("R_max_width: ", r_max_width)
            left_data  = EncodeDistanceData(l_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)
            center_data  = EncodeDistanceData(c_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)
            right_data  = EncodeDistanceData(r_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)

            # Object Tracking Location

            status_data = "0" # Add statements for using the status light if an error is detected
            battery_data  = "0"

            serial_data_package = '00000'

            # Battery ----------------------------------------
            if battery_connected:

                # Only want to send data when the battery level has changed
                battery_capacity = readCapacity(bat_bus)
                battery_state = "0"
                
                if battery_capacity > 75:
                    battery_state = "4"
                elif battery_capacity > 50:
                    battery_state = "3"
                elif battery_capacity > 25:
                    battery_state = "2"
                else:
                    battery_state = "1"

                print("Battery State:", battery_state)
                # Update the battery state if it has changed
                if battery_state != previous_battery_state:
                    previous_battery_state = battery_state
            else:
                battery_capacity = -1
                battery_state = "0"
                battery_data = battery_state
 
            serial_data_package = left_data + center_data + right_data + status_data + battery_data
            print("Serial Data: ", serial_data_package)

            '''
            # TODO: uncomment block
            # Send Serial Data
            if serial_connected: 
                # Passing Edge Case for the right or left.  TODO check if this is accurate

                # Overwrite left or right detection data sent from Jetson to Arduino Micro
                # Cyclist's left side [object is passing close left (cyclist rear POV)]
                if lcr_history[obj_meta.object_id]['brv'][0] >= (1280 - 128) and lcr_history[obj_meta.object_id]['delta_h'] > 0:
                    serial_data_package = "1" + serial_data_package[1:]
                    print("Serial Data: ", serial_data_package)
                    uart_transmission.send(serial_data_package)
                    #location = 'Pass on Left'

                # Cyclist's right side [object is passing close right (cyclist rear POV)]
                elif lcr_history[obj_meta.object_id]['tlv'][0] <= 128 and lcr_history[obj_meta.object_id]['delta_h'] > 0:
                    serial_data_package = serial_data_package[:1] + "1" + serial_data_package[3:]
                    print("serial Data: ", serial_data_package)
                    uart_transmission.send(serial_data_package)
                    #location = 'Pass on Right'

                else:
                    # object is not passing
                    uart_transmission.send(serial_data_package)
            '''
            
            uart_transmission.send(serial_data_package)
        
            # # Clean out the history dictionary of all of the objects that were moving away.
            # for key, value in lcr_history.copy().items() :
            #     if value['delta_w'] < 0:
            #         lcr_history.pop(key)

        # If obj_meta is None
        else:
            try:
                l_frame=l_frame.next
                continue
            except StopIteration:
                break

            
            # if serial_connected:
            #     uart_transmission.send("")
            
        # Clean out the history dictionary of all of the objects that were moving away.
        for key, value in lcr_history.copy().items() :
            if value['delta_w'] < 0:
                lcr_history.pop(key)
                
        # Setting display text to be shown on screen ---------------------------------------------------------------------
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        
        
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.

        # Change width to distance after calibration
        py_nvosd_text_params.display_text = "ID: {} | L:{} C:{} R:{} | Serial Data: {} | Battery {:.1f}%".format(object_id, left_data,center_data,right_data , serial_data_package, battery_capacity)

        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 12
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        # Using pyds.get_string() to get display_text as string
        print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        try:
            l_frame=l_frame.next
        except StopIteration:
            break
    
    
    return Gst.PadProbeReturn.OK	


def cb_newpad(decodebin, decoder_src_pad,data):
    print("In cb_newpad\n")
    caps=decoder_src_pad.get_current_caps()
    gststruct=caps.get_structure(0)
    gstname=gststruct.get_name()
    source_bin=data
    features=caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    print("gstname=",gstname)
    if(gstname.find("video")!=-1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        print("features=",features)
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad=source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")

def decodebin_child_added(child_proxy,Object,name,useright_data):
    print("Decodebin child added:", name, "\n")
    if(name.find("decodebin") != -1):
        Object.connect("child-added",decodebin_child_added,useright_data)


def create_source_bin(index,uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name="source-bin-0"
    print(bin_name)
    nbin=Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin=Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri",uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added",cb_newpad,nbin)
    uri_decode_bin.connect("child-added",decodebin_child_added,nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin,uri_decode_bin)
    bin_pad=nbin.add_pad(Gst.GhostPad.new_no_target("src",Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin


def main(args):
    global pipeline
    global bus
    global loop
    global input_file 
    global flashdrive_connected

    message = None

    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)
 
    # Start of Pipeline Setup -----------------------------------------------------------------------------------------------------------------------
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    # Enable Message forwarding so we can recieve filesinks EOS signal to avoid closing the pipeline before buffers flush and corrupting the mp4 file
    pipeline.set_property('message-forward', True)

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")
    pipeline.add(streammux)

    # If input parameter is passed via an argument then use that as the input source and not the CSI camera.
    if input_file is not None:
        
        
        i = 1 # Number of sources
        print("Creating source_bin ",i," \n ")
        uri_name = "file://" + input_file

        if uri_name.find("rtsp://") == 0 :
            is_live = True

        source_bin=create_source_bin(i, uri_name)
        
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        
        pipeline.add(source_bin)
        padname="sink_3"
        print("padname: ", padname)

        #TODO Determine if a video convert is needed to turn 1080p video into 720p video
        
        file_in_sinkpad= streammux.get_request_pad(padname) 
        if not file_in_sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        
        srcpad_bin=source_bin.get_static_pad("src")
        if not srcpad_bin:
            sys.stderr.write("Unable to create src pad bin \n")
        
        srcpad_bin.link(file_in_sinkpad)

    
    else:
        # Source element for csi camera 
        print("Creating Source \n ")
        source = Gst.ElementFactory.make("nvarguscamerasrc", "src-elem")
        if not source:
            sys.stderr.write(" Unable to create Source \n")
        source.set_property('bufapi-version', True)

        # Converter to scale the image
        nvvidconv_src = Gst.ElementFactory.make("nvvideoconvert", "convertor_src")
        if not nvvidconv_src:
            sys.stderr.write(" Unable to create nvvidconv_src \n")

        # Caps for NVMM and resolution scaling
        caps_nvvidconv_src = Gst.ElementFactory.make("capsfilter", "nvmm_caps2")
        if not caps_nvvidconv_src:
            sys.stderr.write(" Unable to create capsfilter \n")

    

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    # Use Converter to convert from NV12 to RGBA as required by nvosd
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "converter")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")
    
    # Use Converter 
    nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    if not nvvidconv_postosd:
        sys.stderr.write(" Unable to create nvvidconv_postosd \n")

    # Create a caps filter for NVMM and resolution scaling
    caps_nvvidconv_postosd = Gst.ElementFactory.make("capsfilter", "filter")
    caps_nvvidconv_postosd.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

    # Define a Tee to branch the Queue for Recording and one for OSD
    tee = Gst.ElementFactory.make("tee","nvsink-tee")
    if not tee:
        sys.stderr.write(" Unable to create nvsink-tee\n")
    
    queue_1 = Gst.ElementFactory.make("queue", "nvtee-queue")
    if not queue_1:
        sys.stderr.write(" Unable to create queue_1\n")
    
    # Pipeline for File sink
    # Define seperate queue so that each stream can flow independently. required by tee
    queue_2 = Gst.ElementFactory.make("queue","nvtee-queue2")
    if not queue_2:
        sys.stderr.write(" Unable to create queue_2\n")
    #queue2.set_property("flush-on-eos",True) # maybe needed to flush the buffer possibly losing some data to ensure that mp4 is saved if encoding is slow

    # TODO Add third queue (leaky) and branch off from tee and connect to APPSINK
    

    # File save element definitioons -----------------------------------------------------------------------------------------
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "filesave-encoder")
    if not encoder:
        sys.stderr.write(" Unable to create encoder")
    encoder.set_property('bitrate', 4000000)
    
    if is_aarch64():
        # encoder.set_property('preset-level', 1)
        # encoder.set_property('insert-sps-pps', 1)
        if input_file == None:
            encoder.set_property('bufapi-version', 1)


    # changes from h264parse to mpeg4videoparse for debugging.
    video_parser = Gst.ElementFactory.make("h264parse", "filesave-parser")
    if not video_parser:
        sys.stderr.write(" Unable to create parser\n")
    # video_parser.set_property('config-interval', -1) # TODO See if this helps the issue of unreadable mp4 file if not remove.

    #mpegtsmux (previously: mp4mux) or qtmux
    container = Gst.ElementFactory.make("matroskamux","filesave-muxer")
    if not container:
        sys.stderr.write(" Unable to create filesave-muxer\n")
    
    
    filesink_mp4 = Gst.ElementFactory.make("filesink","filesave-sink")
    if not filesink_mp4:
        sys.stderr.write(" Unable to create filesink\n")
    

    current_time = time.localtime()
    current_time = time.strftime("%b-%d-%Y_%H-%M-%S", current_time)

    filesink_mp4.set_property("location","/home/team3/Videos/Ride_Videos/"+ current_time +".mkv")
    filesink_mp4.set_property("sync", True) # Was 1 ,Works with 0
    filesink_mp4.set_property("async", False)# was 0, works with 1


    if (no_display):
        print("Creating Fake Sink")
        sink = Gst.ElementFactory.make("fakesink","fakesink")
        if not sink:
            sys.stderr.write("Unable to create fakesink \n")
        sink.set_property('sync', True)
        sink.set_property('async', False)

    else:
        # Define Sink (This is for On Screen Display) for jetson prefomance boost nvoverlaysink
        print("Creating OverlaySink \n")

        # TODO check if this is faster for rendering the window display
        transform = Gst.ElementFactory.make("nvegltransform",  "nvegl-transform") 
        if not transform:
            sys.stderr.write(" Unable to create nvelgtransform \n")
            
        #sink = Gst.ElementFactory.make("nvoverlaysink", "nvvideo-renderer")
        sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
        sink.set_property('sync', True)
        sink.set_property('async', False)
        if not sink:
            sys.stderr.write(" Unable to create egl sink \n")


    
   
    
    # Define Streammux Properties
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)
    
    if input_file is None:
        streammux.set_property('live-source',1) # Added for CSI
        sys.stderr.write(" Setting Streammux for live-source \n")
        caps_nvvidconv_src.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM), width=1280, height=720'))


    #Set properties of pgie
    pgie.set_property('config-file-path', PGIE_CONFIG_FILE)
   
    #Set properties of tracker
    config = configparser.ConfigParser()
    config.read(TRACKER_CONFIG_FILE)
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        if key == 'enable-past-frame' :
            tracker_enable_past_frame = config.getint('tracker', key)
            tracker.set_property('enable-past-frame', tracker_enable_past_frame)
        if key == 'display-tracking-id' :
            tracker_display_tracking_id = config.getint('tracker', key)
            tracker.set_property('display-tracking-id',tracker_display_tracking_id)

    # Define the pipeline  TODO: Add statements for file input and no display.
    print("Adding elements to Pipeline \n")
    # pipeline.add(source)

    if input_file == None:
        # CSI Camera Input 
        pipeline.add(source)
        pipeline.add(nvvidconv_src)
        pipeline.add(caps_nvvidconv_src)

    # pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    if not no_display: # If there is a display add transform element to pipeline
        pipeline.add(transform)
    pipeline.add(tee)
    pipeline.add(nvvidconv_postosd)
    pipeline.add(encoder)
    pipeline.add(video_parser)
    pipeline.add(caps_nvvidconv_postosd)
    pipeline.add(queue_1)
    pipeline.add(queue_2)
    pipeline.add(container)
    pipeline.add(filesink_mp4)
    
    sinkpad_streammux = streammux.get_request_pad("sink_0")
    if not sinkpad_streammux:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")
    sink.set_property('sync', False)

    # we link the elements together
    print("Linking elements in the Pipeline \n")
    
    if input_file == None:
        print("Linking Camera Input Pipeline")
        source.link(nvvidconv_src)
        nvvidconv_src.link(caps_nvvidconv_src)

        srcpad_caps_nvvidconv_src = caps_nvvidconv_src.get_static_pad("src")
        if not srcpad_caps_nvvidconv_src:
            sys.stderr.write(" Unable to get source pad of source \n")

        # Linking the nv vidconverter src pad to the streammux sink pad.
        srcpad_caps_nvvidconv_src.link(sinkpad_streammux) 

    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(tee) 

    
    # Define the source pads of the tee.
    tee_src1 = tee.get_request_pad('src_%u')
    print("Obtained request pad {} for stream branch".format(tee_src1.get_name()))
    tee_src2 = tee.get_request_pad('src_%u')
    print("Obtained request pad {} for stream branch".format(tee_src2.get_name()))
    if not tee_src1 or not tee_src2:
        sys.stderr.write(" Unable to create tee src 1 or 2 \n")

    # Link tee source pad to queue sink pad and create sink pads for queue 1 and queue 2
    # --> [sink   tee   src] --> [sink  queue  src] -->
    # Link tee src1 to queue 1 
    sink_pad_queue_1 = queue_1.get_static_pad("sink")
    tee_src1.link(sink_pad_queue_1)
    # Link tee src2 to queue 2
    sink_pad_queue_2 = queue_2.get_static_pad("sink")
    tee_src2.link(sink_pad_queue_2)
    if not sink_pad_queue_1 or not sink_pad_queue_2:
        sys.stderr.write(" Unable to create sink pads of queue 1 or queue 2 \n")
    

    # File Record Pipeline linking (Queue_2)
    queue_2.link(nvvidconv_postosd)
    nvvidconv_postosd.link(caps_nvvidconv_postosd)
    caps_nvvidconv_postosd.link(encoder)
    encoder.link(video_parser)

    # Request video sink pad for container 
    container_sink=container.get_request_pad("video_0")
    if not container_sink:
        sys.stderr.write("Unable to create sink pad of container \n")
    

    video_parser_src = video_parser.get_static_pad("src")
    if not video_parser_src:
        sys.stderr.write("Unable to get src pad from video parser \n")
    

    video_parser_src.link(container_sink)
    container.link(filesink_mp4)

    # OSD Render Pipeline
    if is_aarch64() and not no_display:

        #queue_1.link(sink)
        queue_1.link(transform)
        transform.link(sink)
    else: # Can probably remove this. Will only run on aarch64()
        nvosd.link(sink)
    
    # End of Pipeline Setup -----------------------------------------------


    
    # Print the debug dot file for the Gst pipeline graph. Location /tmp/pipeline -created when program runs.
    Gst.debug_bin_to_dot_file(pipeline, Gst.DebugGraphDetails.ALL, "pipeline")

    
    # create and event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    # loop = GLib.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ('message', bus_call, loop)
    
    

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd \n")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # TODO add probe for file input to see when idle so that it can determine when file is done playing.

    print("Starting pipeline \n")

    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
      loop.run()
    except:
        pass


    
    print("Quiting the Loop")
    # loop.quit()
    # loop.unref()
    print("Sending an EOS event to the pipeline")
    pipeline.send_event(Gst.Event.new_eos())
    

    # Wait for EOS before closing the pipeline Gst.CLOCK_TIME_NONE -> poll indefinitly untill message (EOS) is recieved
    # this function will block forever until a matching message was posted on the bus.
    # print("Pausing the pipeline")
    # pipeline.set_state(Gst.State.PAUSED)

    # event = Gst.Event.new_eos()
    #Gst.Element.send_event(pipeline, event)

    # Wait for 10 seconds if the EOS from downstream somehow gets terminated before reaching head it will hand. Forcing EOS will possibly corrupt mp4
    print("Waiting for the EOS message on the bus")
    bus.timed_pop_filtered(10000000000, Gst.MessageType.EOS)
    print("Stopping pipeline")
    
    # cleanup Pipeline and Serial Port and GPIO
    pipeline.set_state(Gst.State.NULL)
    if serial_connected:
        uart_transmission.serial_cleanup()
    if gpio_connected:
        GPIO.cleanup()

    return 0


    



    

# Parse and validate input arguments
def parse_args():
    parser = OptionParser()
    parser.add_option("-i", "--input-file", dest="input_file",default=None,
                      help="Set the input H264 file, Default=None -> CSI Camera", metavar="FILE")
    
    parser.add_option("", "--no-display", action="store_true",
                      dest="no_display", default=False,
                      help="Disable display")
    
    # parser.add_option("", "--batt-con", action="store_false",
    #                   dest="battery_connected", default=False,
    #                   help="")

    # parser.add_option("", "--no-display", action="store_true",
    #                   dest="no_display", default=False,
    #                   help="Disable display")
    (options, args) = parser.parse_args()


    global input_file
    global no_display
    global battery_connected
    global serial_connected

    input_file = options.input_file
    
    print(input_file)
    no_display = options.no_display

   
    return 0

# Use this exit call
def exit_call2():
    print("Quiting the Loop")
    loop.quit()
    return 0



# Software call to exit the program
def exit_call():
    global pipeline
    global bus
    global loop

    
    pipeline.send_event(Gst.Event.new_eos())
    print("Waiting for the EOS message on the bus")
    bus.timed_pop_filtered(5000000000, Gst.MessageType.EOS)
    print("Stopping pipeline")
    pipeline.set_state(Gst.State.NULL)
    print("Program Exited Sucessfully")
    
#     return 0

# # Bus message handeling 
# def bus_call(bus, message, loop):
#     global g_eos_list
#     t = message.type
#     if t == Gst.MessageType.EOS:
#         sys.stdout.write("End-of-stream\n")
#         loop.quit()
#     elif t==Gst.MessageType.WARNING:
#         err, debug = message.parse_warning()
#         sys.stderr.write("Warning: %s: %s\n" % (err, debug))
#     elif t == Gst.MessageType.ERROR:
#         err, debug = message.parse_error()
#         sys.stderr.write("Error: %s: %s\n" % (err, debug))
#         loop.quit()
#     elif t == Gst.MessageType.ELEMENT:
#         struct = message.get_structure()
#         #Check for stream-eos message
#         if struct is not None and struct.has_name("stream-eos"):
#             parsed, stream_id = struct.get_uint("stream-id")
#             if parsed:
#                 #Set eos status of stream to True, to be deleted in delete-sources
#                 print("Got EOS from stream %d" % stream_id)
#                 g_eos_list[stream_id] = True
#     return True


# def stop_release_source(source_id):
#     global g_num_sources
#     global g_source_bin_list
#     global streammux
#     global pipeline

#     #Attempt to change status of source to be released 
#     state_return = g_source_bin_list[source_id].set_state(Gst.State.NULL)

#     if state_return == Gst.StateChangeReturn.SUCCESS:
#         print("STATE CHANGE SUCCESS\n")
#         pad_name = "sink_%u" % source_id
#         print(pad_name)
#         #Retrieve sink pad to be released
#         sinkpad = streammux.get_static_pad(pad_name)
#         #Send flush stop event to the sink pad, then release from the streammux
#         sinkpad.send_event(Gst.Event.new_flush_stop(False))
#         streammux.release_request_pad(sinkpad)
#         print("STATE CHANGE SUCCESS\n")
#         #Remove the source bin from the pipeline
#         pipeline.remove(g_source_bin_list[source_id])
#         source_id -= 1
#         g_num_sources -= 1

if __name__ == '__main__':
    ret = parse_args()
    # If argument parsing fails, returns failure (non-zero)
    if ret == 1:
        sys.exit(1)
    
    sys.exit(main(sys.argv))

