# TIRE'd Eyes

import time
import cv2 as cv

class BikeCam():
    # Define Video Parameters and begin recording
    def __init__(self, filename, resolution, vid_format, window, fps):
        self.FILENAME   = filename
        self.RESOLUTION = resolution
        self.VID_FORMAT = vid_format    # MP4 & AVI; AVI is widely used due to cross-platform compatibility
        self.WINDOW     = window        # Time window, save the last X amount
        self.FPS        = fps           # IMX219-160 camera max = 30 fps

        self.cap        = cv.VideoCapture(0)
        self.start      = time.time()

        # used to save last minute window 
        self.frames_queue = []

        # begin recording
        self.__start()

    # Set Pixel Dimensions based on resolution
    def __setDimensions(self):
        # common resolutions
        RESOLUTIONS = {
            '480p' : (640, 480),
            '780p' : (1280, 720),
            '1080' : (1920, 1080),
        }

        # check to see if resolution exists
        if self.RESOLUTION in RESOLUTIONS:
            width, height =  RESOLUTIONS[self.RESOLUTION]
        else:
            # default to 480p
            width, height = RESOLUTIONS['480p']

        # define video dimensions
        self.cap.set(3, width)
        self.cap.set(4, height)

        return width, height

    # Encoded Video [encodings: https://www.fourcc.org/]
    def __setVideoType(self):
        VIDEO_TYPE = {
            'avi' : cv.VideoWriter_fourcc(*'XVID'),
            'mp4' : cv.VideoWriter_fourcc(*'mp4v')
        }

        # check if video format exists
        if self.VID_FORMAT in VIDEO_TYPE:
            return VIDEO_TYPE[self.VID_FORMAT]
        else:
            return VIDEO_TYPE['avi']

    # Convert frames stored in frames_queue into a video and save to directory 
    def __convertFrameToVideo(self):
        # get current time
        ct = time.localtime()
        ct = time.strftime("%b-%d-%Y_%H:%M:%S", ct)
        
        # initialize CV video_writer
        out = cv.VideoWriter(
            f"{self.FILENAME}_{ct}.{self.VID_FORMAT}", 
            self.__setVideoType(), 
            self.FPS, 
            self.__setDimensions()
        )
        
        # convert frames to video
        for i in range(len(self.frames_queue)):
            out.write(self.frames_queue[i])

        # save to directory
        out.release()

    # Start video capture
    def __start(self):
        # keep track of time for video capture every 5 mins
        while self.cap.isOpened():
            ret, frame = self.cap.read() 
            
            # if frame is available
            if ret == True: 
                # display frame
                cv.imshow('frame', frame)
                
                # append frame
                self.frames_queue.append(frame)

                # moving window
                if time.time() - self.start > self.WINDOW:
                    # remove frames that are out of the time window 
                    self.frames_queue.pop(0)   # first in, first out

                # break on keybind
                k = cv.waitKey(20)
                if k == ord('q'):
                    break

            else:   
                # frame not available
                break

        # TODO: determine whether to patch up video before or after sequence
        self.__convertFrameToVideo()

        self.cap.release()
        cv.destroyAllWindows()

if __name__ == "__main__":
    B = BikeCam(
        filename    = 'video',
        resolution  = '480p',
        vid_format  = "mp4",
        window      = 540,      # TODO: fix frames
        fps         = 25.0
    )