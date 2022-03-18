#!/usr/bin/env python3
import sys

sys.path.append('../')
import platform
import configparser

import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call

import pyds

# Eric: Set the class IDs for the primary neural net
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
past_tracking_meta = [0]


def osd_sink_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    # Initializing object counter with 0.
    obj_counter = {
        PGIE_CLASS_ID_VEHICLE: 0,
        PGIE_CLASS_ID_PERSON: 0,
        PGIE_CLASS_ID_BICYCLE: 0,
        PGIE_CLASS_ID_ROADSIGN: 0
    }
    num_rects = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    ''' 
        
        Integration goes here
        TODO:
            Closest object per segment (Width of BB as first metric. Then, if two objects are in same segment, compare BB center Y coords)
                Distance function based on collected data (Width of obj in center segment of frame)
                FDU LED Control 
                    Includes system status LEDs
            Accelerometer UART tie in for cutting off/saving ride recording
            Other stuff TBD
    '''

    # Get the batch of metadata from the buffer. Do not touch.
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    '''
    NvDsObjectMeta
        class_id: int, Index of the object class infered by the primary detector/classifier
        object_id: int, Unique ID for tracking the object. @ref UNTRACKED_OBJECT_ID indicates the object has not been tracked
        detector_bbox_info: NvDsComp_BboxInfo, Holds a structure containing bounding box parameters of the object when detected by detector
        tracker_bbox_info: NvDsComp_BboxInfo, Holds a structure containing bounding box coordinates of the object when processed by tracker

    NvDsVehicleObject
    '''

    # We know that each frame coming in has the same dimensions for 720p capture
    STANDARD_FRAME_WIDTH = 1280
    STANDARD_FRAME_HEIGHT = 720

    # This lets us statically define the LCR regions
    # These numbers reflect that fact That we're looking behind us. Hence right is on the left of the frame.
    RIGHT = (0, STANDARD_FRAME_WIDTH / 3)
    CENTER = (STANDARD_FRAME_WIDTH / 3, 2 * (STANDARD_FRAME_WIDTH / 3))

    #[frame zero, frame one]

    # Eric: I think L frame contains the current frame metadata for the objects detected and the objects being tracked.
    # Get the list of frame meta objects from the batch meta object.
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:

        # Lists for objects detected in LRC regions
        left_det, center_det, right_det = [], [], []

        try:
            # Cast current frame to an accessible metadata format
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        # Frame number from within the batch. Could be overall frame number
        frame_number = frame_meta.frame_num

        # The number of objects is the number of bounding boxes
        num_rects = frame_meta.num_obj_meta

        # Get a list of the objects in frames' metadata
        l_obj = frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Cast l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)

                '''Could this cause pipeline issues if we try to cast the same thing twice?'''
                # Gets the predicted direction of a given object within the frame
                obj_direction = pyds.NvDsAnalyticsObjInfo.cast(l_obj.data).dirStatus

            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break

            # Dive through casts to get the object's bounding box top left vertex, width, and height?
            #obj_bb_coords = pyds.NvBbox_Coords.cast(pyds.NvDsComp_BboxInfo.cast(obj_meta.tracker_bbox_info))
            obj_bb_coords = obj_meta.tracker_bbox_info.org_bbox_coords

            # Assuming the above is correct, construct the bb for this object.
            obj_tlv = (obj_bb_coords.left, obj_bb_coords.top)
            obj_brv = (obj_bb_coords.left + obj_bb_coords.width, obj_bb_coords.top - obj_bb_coords.height)
            obj_center_coords = ((obj_tlv[0] + obj_brv[0]) / 2, (obj_tlv[1] + obj_brv[1]) / 2)

            # For the purpose of object distance calculation and position, we care mostly about bb width and bb center location
            info_tuple = (obj_bb_coords.width, obj_center_coords, obj_meta.object_id)

            # Based on where the center of the bb of the object is, we classify it as being in either the L,C, or R segment of the frame
            '''
                The away value assumes that the dirStatus field could have such a value.
                No concrete examples were shown for what directions are possible.
            '''
            if obj_direction is not 'away':
                if obj_center_coords[0] < RIGHT[1]:
                    right_det.append(info_tuple)
                elif obj_center_coords >= CENTER[0] and obj_center_coords < CENTER[1]:
                    center_det.append(info_tuple)
                else:
                    left_det.append(info_tuple)
            
        '''Once we see these working, we can make this a function, since it's blatant copy and paste for each list'''
        # This variable is taller than the frame, meaning the center of any bb must be below it
        # This allows us to gradually look for the minimum bb center y coord in each list
        Y_MIN = 721
        l_min_buff, cent_min_buff, r_min_buff = [], [], []
        for info_t in left_det:

            # If the y coord of a bb's center is strictly lt Y_MIN, it must be closer by our standard
            # Therefore, we can clear the list of all other entries and put the new lowest into the list
            if info_t[1][1] < Y_MIN:
                l_min_buff.clear()
                l_min_buff.append(info_t)
                Y_MIN = info_t[1][1]
            
            # We have to be careful of objects who's bbs are at a similar y coordinate, but aren't actually equidistant in reality
            # A car that's far away, but in the center of a frame may have a similar bb center coord to a car that's near to us and in the center of the frame
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
        # Ratio of bb width to width of the frame
        # Serves as a rudimentary form of how close an object is
        l_coeff = l_max_width / STANDARD_FRAME_WIDTH
        r_coeff = r_max_width / STANDARD_FRAME_WIDTH
        c_coeff = c_max_width / STANDARD_FRAME_WIDTH

        # Closest per segment known here
            # Update FDU

        ''' 
            
            Integration ends goes here
        
        '''

        # Eric: We then display the objects detected on the screen.

        # Acquiring a display meta object. The memory ownership remains in
        # the C code so downstream plugins can still access it. Otherwise
        # the garbage collector will claim it when this probe function exits.
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        # Setting display text to be shown on screen
        # Note that the pyds module allocates a buffer for the string, and the
        # memory will not be claimed by the garbage collector.
        # Reading the display_text field here will return the C address of the
        # allocated string. Use pyds.get_string() to get the string content.
        py_nvosd_text_params.display_text = "Frame Number={} Number of Objects={} Vehicle_count={} Person_count={}".format(
            frame_number, num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE], obj_counter[PGIE_CLASS_ID_PERSON])

        # Now set the offsets where the string should appear
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)
        # Using pyds.get_string() to get display_text as string
        print(pyds.get_string(py_nvosd_text_params.display_text))
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        # Eric: Set l frame to be the next frame.
        try:
            l_frame = l_frame.next
        except StopIteration:
            break
    # past tracking metadata
    # Lets not use past data. Only concerned with Now for traffic detection.
    if (past_tracking_meta[0] == 1):
        l_user = batch_meta.batch_user_meta_list
        while l_user is not None:
            try:
                # Note that l_user.data needs a cast to pyds.NvDsUserMeta
                # The casting is done by pyds.NvDsUserMeta.cast()
                # The casting also keeps ownership of the underlying memory
                # in the C code, so the Python garbage collector will leave
                # it alone
                user_meta = pyds.NvDsUserMeta.cast(l_user.data)
            except StopIteration:
                break
            if (user_meta and user_meta.base_meta.meta_type == pyds.NvDsMetaType.NVDS_TRACKER_PAST_FRAME_META):
                try:
                    # Note that user_meta.user_meta_data needs a cast to pyds.NvDsPastFrameObjBatch
                    # The casting is done by pyds.NvDsPastFrameObjBatch.cast()
                    # The casting also keeps ownership of the underlying memory
                    # in the C code, so the Python garbage collector will leave
                    # it alone
                    pPastFrameObjBatch = pyds.NvDsPastFrameObjBatch.cast(user_meta.user_meta_data)
                except StopIteration:
                    break
                for trackobj in pyds.NvDsPastFrameObjBatch.list(pPastFrameObjBatch):
                    print("streamId=", trackobj.streamID)
                    print("surfaceStreamID=", trackobj.surfaceStreamID)
                    for pastframeobj in pyds.NvDsPastFrameObjStream.list(trackobj):
                        print("numobj=", pastframeobj.numObj)
                        print("uniqueId=", pastframeobj.uniqueId)
                        print("classId=", pastframeobj.classId)
                        print("objLabel=", pastframeobj.objLabel)
                        for objlist in pyds.NvDsPastFrameObjList.list(pastframeobj):
                            print('frameNum:', objlist.frameNum)
                            print('tBbox.left:', objlist.tBbox.left)
                            print('tBbox.width:', objlist.tBbox.width)
                            print('tBbox.top:', objlist.tBbox.top)
                            print('tBbox.right:', objlist.tBbox.height)
                            print('confidence:', objlist.confidence)
                            print('age:', objlist.age)
            try:
                l_user = l_user.next
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

    # Eric: Define the Gst Elements. We will configure them later.
    # Source element for reading from the file
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

    sgie1 = Gst.ElementFactory.make("nvinfer", "secondary1-nvinference-engine")
    if not sgie1:
        sys.stderr.write(" Unable to make sgie1 \n")

    # sgie2 = Gst.ElementFactory.make("nvinfer", "secondary2-nvinference-engine")
    # if not sgie1:
    #    sys.stderr.write(" Unable to make sgie2 \n")

    # sgie3 = Gst.ElementFactory.make("nvinfer", "secondary3-nvinference-engine")
    # if not sgie3:
    #    sys.stderr.write(" Unable to make sgie3 \n")

    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    # Create OSD to draw on the converted RGBA buffer
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")

    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    # Finally render the osd output
    if is_aarch64():
        transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")

    print("Creating EGLSink \n")
    sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    if not sink:
        sys.stderr.write(" Unable to create egl sink \n")

    source.set_property('bufapi-version', True)

    caps_nvvidconv_src.set_property('caps', Gst.Caps.from_string('video/x-raw(memory:NVMM), width=1280, height=720'))

    streammux.set_property('width', 1280)
    streammux.set_property('height', 720)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    # Set properties of pgie and sgie
    pgie.set_property('config-file-path', "dstest2_pgie_config.txt")
    sgie1.set_property('config-file-path', "dstest2_sgie1_config.txt")
    sgie2.set_property('config-file-path', "dstest2_sgie2_config.txt")
    sgie3.set_property('config-file-path', "dstest2_sgie3_config.txt")

    # Set properties of tracker
    config = configparser.ConfigParser()
    config.read('dstest2_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width':
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height':
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id':
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file':
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file':
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process':
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)

    print("Adding elements to Pipeline \n")
    pipeline.add(source)
    pipeline.add(nvvidconv_src)
    pipeline.add(caps_nvvidconv_src)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(tracker)
    pipeline.add(sgie1)
    pipeline.add(sgie2)
    pipeline.add(sgie3)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)
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
    tracker.link(sgie1)
    sgie1.link(sgie2)
    sgie2.link(sgie3)
    sgie3.link(nvvidconv)
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
    bus.connect("message", bus_call, loop)

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
