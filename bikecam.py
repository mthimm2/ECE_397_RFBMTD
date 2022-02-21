import os
import pickle
import time

import cv2 as cv

from gstreamer import *

class BikeCam():
    # Define Video Parameters and begin recording
    def __init__(self, filename, resolution, vid_format, window, fps):
        self.FILENAME   = filename
        self.RESOLUTION = resolution
        self.VID_FORMAT = vid_format    # MP4 & AVI; AVI is widely used due to cross-platform compatibility
        self.WINDOW     = window        # Time window, save the last X amount
        self.FPS        = fps           # IMX219-160 camera max = 30 fps

        self.cap        = ""

        self.start      = time.time()

        # used to save last minute window 
        self.frames_queue = []

        # begin recording
        self.__start()

    # Convert frames stored in frames_queue into a video and save to directory 
    def __convertFrameToVideo(self):
        # get current time
        ct = time.localtime()
        ct = time.strftime("%b-%d-%Y_%H:%M:%S", ct)

        w = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
        h = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        fps = self.cap.get(cv.CAP_PROP_FPS)

        gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location=test.mkv "
        out = cv.VideoWriter(gst_out, cv.CAP_GSTREAMER, 0, float(fps), (int(w), int(h)))

        # convert frames to video
        for i in range(len(self.frames_queue)):
            print("converting...")
            out.write(self.frames_queue[i])

        # save to directory
        out.release()

    def __ramUsage(self):
        total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        ram_usage = round((used_memory/total_memory) * 100, 2)
        print(f"RAM memory % used: {ram_usage}")
        # print(f"Total memory: {total_memory}")
        # print(f"Used memory: {used_memory}")
        # print(f"Free memory: {free_memory}")

    # start
    def __start(self):
        window_title = "CSI Camera"
        window_handle = cv.namedWindow(window_title, cv.WINDOW_AUTOSIZE)

        self.cap = cv.VideoCapture(gstreamer_pipeline(flip_method=0), cv.CAP_GSTREAMER)
        if self.cap.isOpened():
            try:
                while True:
                    ret, frame = self.cap.read()

                    if cv.getWindowProperty(window_title, cv.WND_PROP_AUTOSIZE) >= 0:
                        cv.imshow(window_title, frame)
                        pass
                    else:
                        print("Window not available, check window handle")
                        break 

                    # append frame
                    self.frames_queue.append(frame)

                    # moving window
                    if time.time() - self.start > self.WINDOW:
                    
                        if time.time() - self.start == self.WINDOW:
                            print("Moving Window Activated")
                            print(f"Window limit reached: {len(self.frames_queue)}")

                        # remove frames that are out of the time window 
                        self.frames_queue.pop(0)   # first in, first out

                    # break with esc or q
                    k = cv.waitKey(10) & 0xFF
                    if k == 27 or k == ord('q'):
                        break

            finally:
                print("Video complete.\nClosing session...")
                self.__convertFrameToVideo()
                self.cap.release()
                cv.destroyAllWindows()

                file = open("test.pkl","wb")
                pickle.dump(self.frames_queue, file)
                file.close()

        else:
            print("Error: Unable to open camera") 

        if KeyboardInterrupt:
            self.__convertFrameToVideo()
            print("Keyboard was stopped with interrupt")           

if __name__ == "__main__":

    # total frames = 15 * 300 = 4500 frames
    # 2.35 gb ram
    B = BikeCam(
        filename    = 'video',
        resolution  = '480p',
        vid_format  = "mp4",
        window      = 300,      # 300 sec = 5 mins (get last 5 mins)
        fps         = 15.0      # personal webcam = 15 fps
    )

'''
    # print(time.time() - self.start, len(self.frames_queue))
    # print(len(self.frames_queue))

    k = cv.waitKey(20)
    if k == ord('q')
        break

'''