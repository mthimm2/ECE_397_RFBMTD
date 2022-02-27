import cv2 as cv
import matplotlib.pyplot as plt

# bounding box will receive the leftmost and rightmost vertices
class BoundingBox():    
    def __init__(self, v, Co):
        self.v      = v     # tlv = top-left vertice, brv = bottom-right vertice
                            # [(tlv, brv), (tlv, brv)...]

        self.Co     = Co    # distance coefficient

        self.img    = None
        self.mp     = None  # mid-point
        self.loc    = []    # location

        # grid segments
        self.left   = None  # x-axis
        self.middle = None
        self.right  = None

        self.far    = None  # y-axis
        self.middle = None
        self.close  = None 

        self.__loadImage()
        self.__findPosition()
        self.__plotBoundingBox()
        self.__determinePosition()
        self.__determineDistance()

        plt.imshow(self.img)
        plt.show()

    def __loadImage(self):
        self.img = cv.imread("images/car.jpg")

        # apply gridlines

        # obtain image dimensions (height, width, channel)
        img_dim = self.img.shape

        # divide image into 3 segements (width)
        x_seg = img_dim[1] / 3
        y_seg = img_dim[0] / 3

        # apply vertical lines for [display purposes only]
        plt.axvline(x_seg)
        plt.axvline(x_seg * 2)

        # apply boundaries for left-center-right & far-middle-close [rear-view]
        self.right  = (0, x_seg)
        self.center = (x_seg, x_seg*2)
        self.left   = (x_seg*2, x_seg*3)

    def __findPosition(self):
        # TODO: apply for multiple detections?

        self.mp = self.__midPoint(self.v[0][0], self.v[0][1], self.v[1][0], self.v[1][1])

        plt.scatter(self.mp[0], self.mp[1], color="lime")

    def __plotBoundingBox(self):
        # gets to form line segments
        top     = (self.v[0], (self.v[1][0], self.v[0][1]))     # uses top-left & modified bottom-right vertice
        bottom  = ((self.v[0][0], self.v[1][1]), self.v[1])  # uses modified top-left and bottom-right vertice
        left    = (self.v[0], (self.v[0][0], self.v[1][1]))
        right   = ((self.v[1][0], self.v[0][1]), self.v[1])

        # convert points into line segment
        top     = (([top[0][0], top[1][0]]), ([top[0][1], top[1][1]]))
        bottom  = (([bottom[0][0], bottom[1][0]]), ([bottom[0][1], bottom[1][1]]))
        left    = (([left[0][0], left[1][0]]), ([left[0][1], left[1][1]]))
        right   = (([right[0][0], right[1][0]]), ([right[0][1], right[1][1]]))

        # input()
        plt.plot(top[0], top[1], color="lime")
        plt.plot(bottom[0], bottom[1], color="lime")
        plt.plot(left[0], left[1], color="lime")
        plt.plot(right[0], right[1], color="lime")

    def __midPoint(self, x1, y1, x2, y2):
        return ((x1+x2)/2, (y1+y2)/2)

    def __determinePosition(self):
        positions = {
            "left"   : self.left, 
            "center" : self.center, 
            "right"  : self.right, 
        }
        
        # determine position
        for pos, coord in positions.items():
            if pos == "left" or pos == "center" or pos == "right":
                if self.mp[0] >= coord[0] and self.mp[0] <= coord[1]:
                    self.loc.append(pos)       

        print(f"Location: {self.loc}")

    def __determineDistance(self):
        # get image width
        img_dim_x = self.img.shape[0]

        # get object width via bounding box vertices
        obj_dim_x = self.v[1][0] - self.v[0][0]

        # obtain distance based on object's pixel ratio to full image * distance coefficient
        dist = (obj_dim_x / img_dim_x) * self.Co

        print(f"Distance {dist}")

if __name__ == "__main__":
    # 631, 403 -> 1020, 540
    #                top-left  bottom-right
    B = BoundingBox(
        v=[(631,390),(1020,540)],     # [(tlv, brv), (tlv, brv)...]
        Co=100
    )    
