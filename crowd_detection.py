import cv2
import numpy as np
# Classes Necessary For Detection
# ---------------------------------------------------------


class MaskObj:
    """
    Mask Object where Object holds key information to detected object
    """

    def __init__(self, left_x, top_y, width, height):
        """
        Mask Object Init
        :param center_x: Center X of Bounding Box
        :param center_y: Center Y of Bounding Box
        """
        self.left_x = left_x
        self.top_y = top_y
        self.width = width
        self.height = height

    def get_x(self):
        return int(self.left_x)

    def get_y(self):
        return int(self.top_y)

    def get_width(self):
        return int(self.width)

    def get_height(self):
        return int(self.height)

    def __str__(self):
        return "Mask Object {left_x:"+self.left_x + ", top_y:" + top_y + "}"



class CrowdDetection:

    def __init__(self, height, width):
        """
        Crowd Detection Module
        """
        self.__height = height
        self.__width = width
        self.__mask = np.zeros((self.__height, self.__width, 3), np.uint8)

    def getMaskingResult(self, maskObj1, maskObj2):
        frame = np.zeros((self.__height, self.__width, 3), np.uint8)
        cv2.rectangle(self.__mask, (maskObj1.get_x(), maskObj1.get_y()), (maskObj1.get_width(
        ), maskObj1.get_height()), (255, 255, 255), -1)
        cv2.rectangle(frame, (maskObj2.get_x(), maskObj2.get_y()), (maskObj2.get_width(
        ), maskObj2.get_height()), (0, 0, 255), -1)
        #cv2.imshow('image',frame)
        #cv2.imshow('img',self.__mask)
        if np.any(np.logical_and(frame, self.__mask)):
            return True
        else:
            return False

# END OF CLASS DEFINITONS
# ---------------------------------------------------------
