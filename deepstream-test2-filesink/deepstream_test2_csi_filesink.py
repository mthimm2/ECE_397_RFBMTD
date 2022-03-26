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
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
import pyds

# Import Battery Module
from battery_module import *
# bat_bus = smbus.SMBus(1)
bat_bus = None


# Import Uart Communication Module
from uart_module import *

# To Print The dot graph Gstreamer pipeline
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv('GST_DEBUG_DUMP_DIR_DIR', '/tmp')

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
history_dict = {}

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
CLOSE_WIDTH = 260
MED_WIDTH = 180
FAR_WIDTH = 130

''' 
Debug Flags
'''

BATTERY_FLAG = False
SERIAL_FLAG = True

''' 
End of Debug Flags
'''

if SERIAL_FLAG:
    # Initialize UART_Jetson Object
    uart_transmission = UART_Jetson()

if BATTERY_FLAG:
    # battery status (hold the last known battery level)
    bat_bus = smbus.SMBus(1)

previous_battery_data = ""


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

        # Lists for objects detected in LRC regions
        left_det, center_det, right_det = [], [], []

        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        
        except StopIteration:
            break

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

            # Used to determine whether or not an object is approaching or receding in frame
            obj_bb_area = obj_bb_coords.height * obj_bb_coords.width

            # Construct the bounding box for this object.
            obj_tlv = (obj_bb_coords.left, obj_bb_coords.top)
            obj_brv = (obj_bb_coords.left + obj_bb_coords.width, obj_bb_coords.top + obj_bb_coords.height)
            obj_center_coords = ((obj_tlv[0] + obj_brv[0]) / 2, (obj_tlv[1] + obj_brv[1]) / 2)

            # For the purpose of object distance calculation and position, we care mostly about bb width and bb center location
            info_tuple = (obj_bb_coords.width, obj_center_coords, obj_bb_area, obj_meta.object_id)
            
            #print(info_tuple)
           
            # Initialize the object and insert it into the dictionary if not already provided : 0 is for car and 2 is for person
            if obj_meta.object_id not in history_dict and obj_meta.class_id is 2:
                history_dict[obj_meta.object_id] = {}
                history_dict[obj_meta.object_id]['delta_w'] = 0
                history_dict[obj_meta.object_id]['delta_h'] = 0
                history_dict[obj_meta.object_id]['direction'] = None
                history_dict[obj_meta.object_id]['width'] = obj_bb_coords.width
                history_dict[obj_meta.object_id]['height'] = obj_bb_coords.height
                history_dict[obj_meta.object_id]['tlv'] = obj_tlv
                history_dict[obj_meta.object_id]['brv'] = obj_brv
                
            elif obj_meta.object_id is 0:
                history_dict[obj_meta.object_id]['delta_w'] = history_dict[obj_meta.object_id]['width'] - obj_bb_coords.width
                history_dict[obj_meta.object_id]['delta_h'] = history_dict[obj_meta.object_id]['height'] - obj_bb_coords.height
                history_dict[obj_meta.object_id]['direction'] = 'left' if obj_tlv[0] > history_dict[obj_meta.object_id]['tlv'][0] else 'right' if obj_tlv[0] != history_dict[obj_meta.object_id]['tlv'][0] else None
                history_dict[obj_meta.object_id]['width'] = obj_bb_coords.width
                history_dict[obj_meta.object_id]['height'] = obj_bb_coords.height
                history_dict[obj_meta.object_id]['tlv'] = obj_tlv
                history_dict[obj_meta.object_id]['brv'] = obj_brv

            # If an object is determined to be approaching us, we allow it to be placed into the 
            # Based on where the center of the bb of the object is, we classify it as being in either the L,C, or R segment of the frame            
            if history_dict[info_tuple[3]]['delta_w'] >= 0:
                if obj_center_coords[0] < RIGHT[1]:
                    right_det.append(info_tuple)
                elif obj_center_coords[0] >= CENTER[0] and obj_center_coords[0] < CENTER[1]:
                    center_det.append(info_tuple)
                else:
                    left_det.append(info_tuple)

            # Clean out the history dictionary of all of the objects that were moving away.
            for key, value in history_dict.items():
                if value['delta_w'] < 0:
                    history_dict.pop(key)

        if obj_meta is not None:

            # Determine closes object in each frame
            l_max_width = max([info_t[0] for info_t in left_det])   if len(left_det)    > 0 else 0
            r_max_width = max([info_t[0] for info_t in right_det])  if len(right_det)   > 0 else 0
            c_max_width = max([info_t[0] for info_t in center_det]) if len(center_det)  > 0 else 0

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
            # 
            # Eric: for testing get the bounding box coeff for the given region
            coeff = [l_max_width, c_max_width, r_max_width]
            location_list = ['Left','Center','Right']
            max_coeff = max(coeff)
            max_index = coeff.index(max_coeff)
            location=location_list[max_index]     

            # Distance estimation function:
            # distance = c_coeff*var 

            '''
            FDU Code:
                L | C | R | S | B | Other Function
                0 | 1 | 2 | 3 | 4 |
                L, C, R  => 0, 1, 2, 3     [0=off, 1=close, 2=med, 3=far]
                S => 0, 1                  [0=off, 1=on]
                B => 0, 1, 2, 3, 4         [0=off, 1 : < 25, 2 : >25,  3 : >50, 4 : >75]
                Other Functions => TBD
            '''

            l_data  = EncodeDistanceData(l_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)
            c_data  = EncodeDistanceData(c_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)
            r_data  = EncodeDistanceData(r_max_width, CLOSE_WIDTH, MED_WIDTH, FAR_WIDTH)


            if BATTERY_FLAG:
                # Battery functions 
                battery_cap = readCapacity(bat_bus)
                battery_data = ""
                
                if battery_data != previous_battery_data:
                    if battery_cap > 75:
                        battery_data = "4"
                    elif battery_cap > 50:
                        battery_data = "3"
                    elif battery_cap > 25:
                        battery_data = "2"
                    else:
                        battery_data = "1"

                    previous_battery_data = battery_data

            # Is the status LED for the battery?
            # if so then update the information scheme as needed
            if BATTERY_FLAG:
                o_data = f"0{battery_data}"   # status (0-1), battery (0-3)
            else:
                o_data = 0

            # l_data=1
            # c_data=2
            # r_data=3

            # Send Serial Data
            if SERIAL_FLAG:
                # Passing Case for the right or left. 

                # Overwrite left or right detection data sent from Jetson to Arduino Micro
                # Cyclist's left side [object is passing close left (cyclist rear POV)]
                if history_dict[obj_meta.object_id]['brv'][0] >= (1280 - 128) and history_dict[obj_meta.object_id]['delta_h'] > 0:
                    uart_transmission.send("1" + c_data + r_data + o_data)

                # Cyclist's right side [object is passing close right (cyclist rear POV)]
                elif history_dict[obj_meta.object_id]['tlv'][0] <= 128 and history_dict[obj_meta.object_id]['delta_h'] > 0:
                    uart_transmission.send(l_data + c_data + "1" + o_data)

                else:
                    # object is not passing
                    uart_transmission.send(l_data + c_data + r_data + o_data)


        # Debug Print of Left Center and Right Coeff
        #print(l_coeff,c_coeff, r_coeff)

        # Closest per segment known here
            # Update FDU

        ''' 
            
            Integration ends goes here
        '''

        # Based on where the center of the bounding box of the object is, we classify it as being in either the L,C, or R segment of the frame
        '''
            The away value assumes that the dirStatus field could have such a value.
            No concrete examples were shown for what directions are possible.
        '''
    

        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta=pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.

        # Change width to distance after calibration
        py_nvosd_text_params.display_text = "Location: {} | Serial Data: {} | Distance Level: {}".format(location,l_data+c_data+r_data, )

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



# TODO Add transfor to be queue for arch 64. 
def main(args):
    global pipeline
    global bus
    global loop

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


    # TODO Implement File Input Inference
    # If input parameter is passed via an argument then use that as the input source and not the CSI camera.
    if input_file != None:
           # Source element for reading from the file
        print("Playing file %s " % input_file)
        source = Gst.ElementFactory.make("filesrc", "file-source")
        if not source:
            sys.stderr.write(" Unable to create file source \n")
        source.set_property('location', input_file)
        # Since the data format in the input file is elementary h264 stream,
        # we need a h264parser
        print("Creating H264Parser \n")
        
        h264parser_input = Gst.ElementFactory.make("h264parse", "h264-parser_input")
        if not h264parser_input:
            sys.stderr.write(" Unable to create h264 parser \n")
        

        # Create a caps filter for NVMM and resolution scaling
        caps_decoder = Gst.ElementFactory.make("capsfilter", "filter")
        caps_decoder.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))


        # Use nvdec_h264 for hardware accelerated decode on GPU|   was nvv4l2decoder trying omxh264dec
        print("Creating Decoder \n")
        decoder = Gst.ElementFactory.make("omxh264dec", "nvv4l2-decoder")
        if not decoder:
            sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")
    
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

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    # Use nvinfer to run inferencing on decoder's output,
    # behaviour of inferencing is set through config file
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    # Use Converter to convert from NV12 to RGBA as required by nvosd
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
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

    

    # Make the h264 encoder
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "h264-encoder")
    if not encoder:
        sys.stderr.write(" Unable to create encoder")
    encoder.set_property('bitrate', 4000000)
    if is_aarch64():
        encoder.set_property('preset-level', 1)
        encoder.set_property('insert-sps-pps', 1)
        if input_file == None:
            encoder.set_property('bufapi-version', 1)

    # Is this really needed? 
    # changes from h264parse to mpeg4videoparse for debugging.  # FIXME h264 parser not working and will hold up the osd. Look into possible hangups in pipeline.
    video_parser = Gst.ElementFactory.make("h264parse", "h264 parser")
    if not video_parser:
        sys.stderr.write(" Unable to create parser\n")
    video_parser.set_property('config-interval', -1) # TODO See if this helps the issue of unreadable mp4 file if not remove.

    
    container = Gst.ElementFactory.make("mp4mux","muxer")
    if not container:
        sys.stderr.write(" Unable to create mp4mux\n")

    filesink_mp4 = Gst.ElementFactory.make("filesink","filesink_video")
    if not filesink_mp4:
        sys.stderr.write(" Unable to create filesink\n")

    current_time = time.localtime()
    current_time = time.strftime("%b-%d-%Y_%H:%M:%S", current_time)
    filesink_mp4.set_property("location","/home/team3/Videos/Video_Out/"+ current_time +".mp4")
    filesink_mp4.set_property("sync",1) # Was 1 ,Works with 0
    filesink_mp4.set_property("async",0)# was 0, works with 1


    if (no_display):
        print("Creating Fake Sink")
        sink = Gst.ElementFactory.make("fakesink","fakesink")
        if not sink:
            sys.stderr.write("Unable to create fakesink \n")
    else:
        # Define Sink (This is for On Screen Display) for jetson prefomance boost nvoverlaysink
        print("Creating OverlaySink \n")

        # TODO check if this is faster for rendering the window display
        transform = Gst.ElementFactory.make("nvegltransform",  "nvegl-transform") 
        if not transform:
            sys.stderr.write(" Unable to create nvelgtransform \n")
            
        #sink = Gst.ElementFactory.make("nvoverlaysink", "nvvideo-renderer")
        sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
        sink.set_property('sync', 0)
        # sink.set_property("overlay-x",0) # 0
        # sink.set_property("overlay-y",360) #360
        # sink.set_property("overlay-w",960) #720
        # sink.set_property("overlay-h",480) #360
        if not sink:
            sys.stderr.write(" Unable to create egl sink \n")


    
    caps_nvvidconv_src.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM), width=1280, height=720'))
    
    # Define Streammux
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)
    
    if input_file == None:
        streammux.set_property('live-source',1) # Added for CSI
        sys.stderr.write(" Setting Streammux for live-source \n")

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
    pipeline.add(source)

    if input_file != None:
        pipeline.add(h264parser_input)
        pipeline.add(decoder)
        pipeline.add(caps_decoder)

    pipeline.add(nvvidconv_src)
    pipeline.add(caps_nvvidconv_src)
    pipeline.add(streammux)
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
    
    # we link the elements together
    print("Linking elements in the Pipeline \n")
    if input_file != None:
        source.link(h264parser_input)
        h264parser_input.link(decoder)
        decoder.link(nvvidconv_src)
    else:
        source.link(nvvidconv_src)
    nvvidconv_src.link(caps_nvvidconv_src)

    sinkpad_streammux = streammux.get_request_pad("sink_0")
    if not sinkpad_streammux:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")

    srcpad_caps_nvvidconv_src = caps_nvvidconv_src.get_static_pad("src")
    if not srcpad_caps_nvvidconv_src:
        sys.stderr.write(" Unable to get source pad of source \n")

    srcpad_caps_nvvidconv_src.link(sinkpad_streammux) # Linking the nv vidconverter src pad to the streammux sink pad.
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
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect ("message", bus_call, loop)
    
    

    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd \n")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    
    print("Starting pipeline \n")

    # start play back and listed to events
    pipeline.set_state(Gst.State.PLAYING)
    try:
      loop.run()
    except:
        print("Sending an EOS event to the pipeline")
        pass

    
    

    # Wait for EOS before closing the pipeline Gst.CLOCK_TIME_NONE -> poll indefinitly untill message (EOS) is recieved
    # this function will block forever until a matching message was posted on the bus.
    pipeline.send_event(Gst.Event.new_eos())
    print("Waiting for the EOS message on the bus")

    # Wait for 5 seconds if the EOS from downstream somehow gets terminated before reaching head it will hand. Forcing EOS will possibly corrupt mp4
    bus.timed_pop_filtered(5000000000, Gst.MessageType.EOS)
    print("Stopping pipeline")
    
    # cleanup Pipeline and Serial Port
    pipeline.set_state(Gst.State.NULL)
    if SERIAL_FLAG:
        uart_transmission.serial_cleanup()



    

# Parse and validate input arguments
def parse_args():
    parser = OptionParser()
    parser.add_option("-i", "--input-file", dest="input_file",default=None,
                      help="Set the input H264 file, Default=None -> CSI Camera", metavar="FILE")
    parser.add_option("", "--no-display", action="store_true",
                      dest="no_display", default=False,
                      help="Disable display")

    (options, args) = parser.parse_args()


    global input_file
    global no_display
    input_file = options.input_file
    no_display = options.no_display

   
    return 0

# Other Exit Call - TODO see if this exits more gracefully
def exit_call2():
    sys.exit(main(sys.argv))
    
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
    
    return 0

# Bus message handeling 
def bus_call(bus, message, loop):
    global g_eos_list
    t = message.type
    if t == Gst.MessageType.EOS:
        sys.stdout.write("End-of-stream\n")
        loop.quit()
    elif t==Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        sys.stderr.write("Warning: %s: %s\n" % (err, debug))
    elif t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        sys.stderr.write("Error: %s: %s\n" % (err, debug))
        loop.quit()
    elif t == Gst.MessageType.ELEMENT:
        struct = message.get_structure()
        #Check for stream-eos message
        if struct is not None and struct.has_name("stream-eos"):
            parsed, stream_id = struct.get_uint("stream-id")
            if parsed:
                #Set eos status of stream to True, to be deleted in delete-sources
                print("Got EOS from stream %d" % stream_id)
                g_eos_list[stream_id] = True
    return True


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

