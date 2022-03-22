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


from asyncio.windows_utils import pipe
import sys
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


# Debug Flags
DISPLAY_ON = 1
RECORD_ON = True


# Class definition
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

# For Debug Print Onto display for data recording.
class_id_names = ["Car","Bicycle","Person","Roadsign","No bBox"]


past_tracking_meta=[0]

def osd_sink_pad_buffer_probe(pad,info,u_data):
   
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return
   
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    # We know that each frame coming in has the same dimensions for 720p capture
    STANDARD_FRAME_WIDTH = 1280
    STANDARD_FRAME_HEIGHT = 720

    # This lets us statically define the LCR regions
    # These numbers reflect that fact That we're looking behind us. Hence right is on the left of the frame.
    RIGHT = (0, STANDARD_FRAME_WIDTH / 3)
    CENTER = (STANDARD_FRAME_WIDTH / 3, 2 * (STANDARD_FRAME_WIDTH / 3))

    #[frame zero, frame one]

    # Debug Default index for class name, Used for Printing out what object is detected on screen.
    class_id_index = 4
    
    # Debug: Set info_tuple default value so if l_obj is None it will be defined when debug is displaying info_tuple name.
    info_tuple = (0,0,0)

    
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:

            # Lists for objects detected in LRC regions
            left_det, center_det, right_det = [], [], []


            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.glist_get_nvds_frame_meta()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            #frame_meta = pyds.glist_get_nvds_frame_meta(l_frame.data)
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        l_obj=frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                #obj_meta=pyds.glist_get_nvds_object_meta(l_obj.data)
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
               

            except StopIteration:
                break

            # Debug for on screen display of class name 
            class_id_index = obj_meta.class_id
            
            obj_meta.rect_params.border_color.set(0.0, 0.0, 1.0, 0.0)
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break
            # Dive through casts to get the object's bounding box top left vertex, width, and height?
            #obj_bb_coords = pyds.NvBbox_Coords.cast(pyds.NvDsComp_BboxInfo.cast(obj_meta.tracker_bbox_info))
            obj_bb_coords = obj_meta.tracker_bbox_info.org_bbox_coords

            # Construct the bounding box for this object.
            obj_tlv = (obj_bb_coords.left, obj_bb_coords.top)
            obj_brv = (obj_bb_coords.left + obj_bb_coords.width, obj_bb_coords.top + obj_bb_coords.height)
            obj_center_coords = ((obj_tlv[0] + obj_brv[0]) / 2, (obj_tlv[1] + obj_brv[1]) / 2)

            # For the purpose of object distance calculation and position, we care mostly about bounding box width and bounding box center location
            info_tuple = (obj_bb_coords.width, obj_center_coords, obj_meta.object_id)
            
            print(info_tuple)
           

            if obj_center_coords[0] < RIGHT[1]:
                right_det.append(info_tuple)

            elif obj_center_coords[0] >= CENTER[0] and obj_center_coords[0] < CENTER[1]:
                center_det.append(info_tuple)

            else:
                left_det.append(info_tuple)

            # print(right_det)
            # print(center_det)
            # print(left_det)

        # This variable is taller than the frame, meaning the center of any bounding box must be below it
        # This allows us to gradually look for the minimum bounding box center y coord in each list
        # Eric: What variable? Also What is the Use Case, like a description of what edge case this is used for?
        Y_MIN = 721
        l_min_buff, cent_min_buff, r_min_buff = [], [], []
        for info_t in left_det:

            # If the y coord of a bounding box's center is strictly lt Y_MIN, it must be closer by our standard
            # Therefore, we can clear the list of all other entries and put the new lowest into the list
            if info_t[1][1] < Y_MIN:
                l_min_buff.clear()
                l_min_buff.append(info_t)
                Y_MIN = info_t[1][1]
            
            # We have to be careful of objects who's bounding boxs are at a similar y coordinate, but aren't actually equidistant in reality
            # A car that's far away, but in the center of a frame may have a similar bounding box center coord to a car that's near to us and in the center of the frame
            # So we need to have a window of similarity in case we run into this situation
            elif Y_MIN - info_t[1][1] <= 0.1 * Y_MIN:
                l_min_buff.append(info_t)
            else:
                pass

        # Center segment min y coord
        for info_t in center_det:
            
            if info_t[1][1] < Y_MIN:
                cent_min_buff.clear()
                cent_min_buff.append(info_t)
                Y_MIN = info_t[1][1]

            elif Y_MIN - info_t[1][1] <= 0.1 * Y_MIN:
                cent_min_buff.append(info_t)
            
            else:
                pass
            # Eric: What is min y coord?
        # Right segment min y coord
        for info_t in right_det:
    
            if info_t[1][1] < Y_MIN:
                r_min_buff.clear()
                r_min_buff.append(info_t)
                Y_MIN = info_t[1][1]
            
            elif Y_MIN - info_t[1][1] <= 0.1 * Y_MIN:
                r_min_buff.append(info_t)

            else:
                pass

        # Determine closes object in each frame
        l_max_width = max([info_t[0] for info_t in l_min_buff]) if len(l_min_buff) > 0 else 0
        c_max_width = max([info_t[0] for info_t in cent_min_buff]) if len(cent_min_buff) > 0 else 0
        r_max_width = max([info_t[0] for info_t in r_min_buff]) if len(r_min_buff) > 0 else 0

        '''
            Do we need to have any special considerations for objects not in the center segment?
            Is this where we make use of the distance coefficient to help compensate for the fish-eyeing?
        '''
        # Ratio of bounding box width to width of the frame
        # Serves as a rudimentary form of how close an object is
        l_coeff = l_max_width / STANDARD_FRAME_WIDTH
        r_coeff = r_max_width / STANDARD_FRAME_WIDTH
        c_coeff = c_max_width / STANDARD_FRAME_WIDTH

        # Dubug width list for data recording. 
        width_list = [l_max_width,c_max_width,r_max_width]
        
        # Eric: for testing get the bounding box coeff for the given region
        coeff = [l_coeff, c_coeff,r_coeff]
        location_list = ['Left','Center','Right']
        max_coeff = max(coeff)
        max_index = coeff.index(max_coeff)
        location=location_list[max_index]

        # Distance estimation function:
        # distance = c_coeff*var 




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
        py_nvosd_text_params.display_text = "Class= {} | Id= {} | Location= {} | bBox_Width= {} | Coeff={} ".format(class_id_names[class_id_index],info_tuple[2],location,width_list[max_index], coeff[max_index])

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

def main(args):
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    # # Source element for file input 
    # sourceFile = Gst.ElementFactory.make("filesrc","file-source")
    # if not sourceFile:
    #     sys.stderr.write(" Unable to create File Source \n")
    
    # # Since the data format in the input file is elementary h264 stream,
    # # we need a h264parser
    # print("Creating H264Parser \n")
    # h264parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    # if not h264parser:
    #     sys.stderr.write(" Unable to create h264 parser \n")

    # # Use nvdec_h264 for hardware accelerated decode on GPU
    # print("Creating Decoder \n")
    # decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")
    # if not decoder:
    #     sys.stderr.write(" Unable to create Nvv4l2 Decoder \n")


    # Source element for csi camera
    print("Creating Source \n ")
    source = Gst.ElementFactory.make("nvarguscamerasrc", "src-elem")
    if not source:
        sys.stderr.write(" Unable to create Source \n")

    # Converter to scale the image
    nvvidconv_src = Gst.ElementFactory.make("nvvideoconvert", "convertor_src")
    if not nvvidconv_src:
        sys.stderr.write(" Unable to create nvvidconv_src \n")

    # Caps for NVMM and resolution scaling
    caps_nvvidconv_src = Gst.ElementFactory.make("capsfilter", "nvmm_caps")
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

    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    # Finally render the osd output using 'queue for jetson pref boost.
    if is_aarch64():
        transform = Gst.ElementFactory.make("queue", "queue")
    
    # Define Sink (This is for On Screen Display) for jetson prefomance boost nvoberlaysink
    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nvoverlaysink", "nvvideo-renderer")
    sink.set_property('sync', 0)
    sink.set_property("overlay-x",0) # 0
    sink.set_property("overlay-y",360) #360
    sink.set_property("overlay-w",960) #720
    sink.set_property("overlay-h",480) #360

    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    # Define file sink Gst streams:
    if RECORD_ON:
        tee = Gst.ElementFactory.make("tee","nvsink-tee")
        if not tee:
            sys.stderr.write(" Unable to create nvsink-tee\n")
        
        queue2 = Gst.ElementFactory.make("queue","nvtee-queue2")
        if not queue2:
            sys.stderr.write(" Unable to create nvtee-queue2\n")


        # unknown if needed 
        nvvidconv2 = Gst.ElementFactory.make("nvvideoconvert", "convertor2")
        if not nvvidconv2:
            sys.stderr.write(" Unable to create nvvidconv2 \n")
        # Dont know what caps or caps filter is
        capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
        if not capsfilter:
            sys.stderr.write(" Unable to create capsfilter \n")

        caps = Gst.Caps.from_string("video/x-raw, format=I420")
        capsfilter.set_property("caps", caps)

        encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
        if not encoder:
            sys.stderr.write(" Unable to create encoder \n")
        encoder.set_property("bitrate", 2000000)

        print("Creating Code Parser \n")
        codeparser = Gst.ElementFactory.make("mpeg4videoparse", "mpeg4-parser")
        if not codeparser:
            sys.stderr.write(" Unable to create code parser \n")

        print("Creating Container \n")
        container = Gst.ElementFactory.make("qtmux", "qtmux")
        if not container:
            sys.stderr.write(" Unable to create code parser \n")

        print("Creating Sink \n")
        sink2 = Gst.ElementFactory.make("filesink", "filesink")
        if not sink:
            sys.stderr.write(" Unable to create file sink \n")

        sink2.set_property("location", "./out.mp4")
        sink2.set_property("sync", 1)
        sink2.set_property("async", 0)
    # Finished Gst file sink streams

    source.set_property('bufapi-version', True)
    caps_nvvidconv_src.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM), width=1280, height=720'))
    
    # Define Streammux
    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)
    streammux.set_property('live-source',1) # Added for CSI


    

    #Set properties of pgie
    pgie.set_property('config-file-path', "dstest2_pgie_config2.txt")
   
    #Set properties of tracker
    config = configparser.ConfigParser()
    config.read('dstest2_tracker_config2.txt')
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

    print("Adding elements to Pipeline \n")
    pipeline.add(source)
    pipeline.add(nvvidconv_src)
    pipeline.add(caps_nvvidconv_src)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
    pipeline.add(tee)
    pipeline.add(queue2)
    pipeline.add()

    if is_aarch64():
        pipeline.add(transform)

    # we link the elements together
    print("Linking elements in the Pipeline \n")
    source.link(nvvidconv_src)
    nvvidconv_src.link(caps_nvvidconv_src)

    sinkpad = streammux.get_request_pad("sink_0")
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")
    srcpad = caps_nvvidconv_src.get_static_pad("src")
    if not srcpad:
        sys.stderr.write(" Unable to get source pad of source \n")

    srcpad.link(sinkpad)
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(nvvidconv)
    nvvidconv.link(nvosd)
    


    if is_aarch64():
        nvosd.link(transform)
        transform.link(sink)
    else:
        nvosd.link(sink)
    
    
        

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
      pass

    # cleanup
    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

