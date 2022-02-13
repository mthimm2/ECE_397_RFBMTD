import os
import time
import cv2 as cv
import keyboard as key

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

    def __ramUsage(self):
        total_memory, used_memory, free_memory = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
        ram_usage = round((used_memory/total_memory) * 100, 2)
        print(f"RAM memory % used: {ram_usage}")
        # print(f"Total memory: {total_memory}")
        # print(f"Used memory: {used_memory}")
        # print(f"Free memory: {free_memory}")

    # Start video capture
    def __start(self):
        # self.__ramUsage()

        # keep track of time for video capture every 5 mins
        while self.cap.isOpened():
            ret, frame = self.cap.read() 
            
            # self.__ramUsage()

            # if frame is available
            if ret == True: 
                # display frame
                # cv.imshow('frame', frame)
                
                # append frame
                self.frames_queue.append(frame)

                # print(time.time() - self.start, len(self.frames_queue))
                
                # moving window
                if time.time() - self.start > self.WINDOW:
                    
                    if time.time() - self.start == self.WINDOW:
                        print("Moving Window Activated")
                        print(f"Window limit reached: {len(self.frames_queue)}")    # 4311

                    # remove frames that are out of the time window 
                    self.frames_queue.pop(0)   # first in, first out
                    
                # break on keybind
                if key.is_pressed("q"):
                    break

            else:   
                # frame not available
                break

        # TODO: determine whether to patch up video before or after sequence
        self.__convertFrameToVideo()

        # self.__ramUsage()

        print("Video complete.\nClosing session...")
        self.cap.release()
        cv.destroyAllWindows()

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

