"""Backend for eye movement tracking.

This module is used to track movements of a single eye which is
assumed to be stationary related to the camera (for example, camera
mounted to visor of a cap). The movements recorded are pupil movement
on horizontal axis and whether the eye is currently blinking or not.

Written by Antti Alastalo, small modifications for Qt integration by
Tuomas Rantataro.
"""
import cv2
import numpy as np

from PySide2.QtCore import QObject, Signal

class Eyetracker(QObject):
    """Class for eye, pupil and blinking detection.

    Usage: use take_snapshot method before running the tracking
    functions detect_blink and track_pupil and draw. They don't call
    it by themselves to allow the same frame to be used for all of
    them, which is the wanted use case.
    """
    eyeChanged = Signal()
    #pupilChanged = Signal()
    #blinkChanged = Signal()
    #resultChanged = Signal()

    def __init__(self):
        super().__init__()
        self.cams = []
        self.init_cameras()
        self.cam = None
        try:
            self.cam = cv2.VideoCapture(self.cams[0])
        except IndexError:
            print('No camera found. Add camera and try again.')

        self.center = (0, 0)
        self.pupil = (0, 0)
        self.img = None
        self.blink_value = 0
        self.blink = False

        self.eye_pic = None
        self.pupil_pic = None
        self.blink_pic = None
        self.result_pic = None

        self.eye_rec = None

        self.frame = None
        self.frame_blurred = None
        self.frame_blurred_bw = None

    def init_cameras(self):
        """Find cameras available.

        OpenCV does not have method for listing cameras so doing a
        brainless loop to find some.
        """
        for i in range(4): # There probably are less than 4 cameras
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                self.cams.append(i)

        print("{} cameras found".format(len(self.cams)))

    def select_camera(self, num):
        """Select camera to use for eye tracking.

        Arguments:
        num -- Index for the camera to use.
        """
        if self.cam:
            self.cam.release()
        try:
            self.cam = cv2.VideoCapture(self.cams[num])
        except IndexError:
            print('selectCamera: Invalid camera number {}', num)

    def take_snapshot(self):
        """Take a picture from video stream

        Take a picture for processing with other methods. Also process
        it to black & white and median blurred for some methods.
        """
        _, self.frame = self.cam.read()
        self.frame_blurred = cv2.medianBlur(self.frame, 5)
        self.frame_blurred_bw = cv2.cvtColor(self.frame_blurred, cv2.COLOR_BGR2GRAY)

    def detect_blink(self):
        """Detect eye blinking

        Detect whether eye is blinking or not. The frame is processed
        to black and white. Pupil shows as black in processed image, so
        blink is detected based on how many white pixels there are. The
        region of interest is bounded by calibration done before.

        Returns True if the users eye is shut and False if it is open.
        """
        frame = self.frame_blurred_bw

        coord_x, coord_y, width, height = \
            self.eye_rec[0], self.eye_rec[1], self.eye_rec[2], self.eye_rec[3]
        _, thresh = cv2.threshold( \
            frame[coord_y:(coord_y+height), coord_x:(coord_x+width)], 70, 250, cv2.THRESH_BINARY)
        thresh = cv2.erode(thresh, np.ones((15, 15), np.uint8), iterations=4)

        self.blink_pic = thresh
        #self.blinkChanged.emit()

        if cv2.countNonZero(thresh) >= self.blink_value:
            self.blink = True
            return True
        self.blink = False
        return False

    def get_bounding_rectangle(self):
        """Find an eye from video frame and save its coordinates.

        Try to find an eye from a picture taken from camera. Stays in
        a forever loop until an eye is found. OpenCV's machine learning
        toolset is used to find the eye by using a pre-trained Haar-
        cascade classifier.

        When an eye is found, updates location of the eye to variable
        self.eye_rec and whole picture used to variable self.eye_pic.
        Also emits a signal to update the image in UI.
        """
        eye_cascade = cv2.CascadeClassifier('./resources/haarcascade_eye.xml')
        eye_found = False
        while not eye_found:
            self.take_snapshot()
            frame = self.frame_blurred
            eyes = eye_cascade.detectMultiScale(frame, 1.2, 1, minSize=(100, 100))
            if len(eyes) > 0:
                (coord_x, coord_y, width, height) = eyes[0]
                self.eye_rec = (int(coord_x-(250-width)/2), int(coord_y-(250-height)/2), 250, 250)
                coord_x2, coord_y2, width2, height2 = \
                    self.eye_rec[0], self.eye_rec[1], self.eye_rec[2], self.eye_rec[3]
                _, thresh = cv2.threshold(\
                    frame[coord_y2:(coord_y2+height2), coord_x2:(coord_x2+width2)], \
                    70, 250, cv2.THRESH_BINARY)
                thresh = cv2.erode(thresh, np.ones((10, 10), np.uint8), iterations=4)
                #self.blink_value = cv2.countNonZero(thresh)+2000
                self.blink_value = 62000
                top_left = (self.eye_rec[0], self.eye_rec[1])
                bottom_right = (self.eye_rec[0] + self.eye_rec[2],\
                                self.eye_rec[1] + self.eye_rec[3])
                self.eye_pic = cv2.rectangle(frame, top_left, bottom_right, (0, 0, 220), 3)
                self.eyeChanged.emit()
                eye_found = True
                break

    def track_pupil(self):
        """Find position of pupil

        Finds the position of the pupil and saves it in self.pupil as a
        tuple (x,y). Also updates image of pupil detection in
        self.pupil_pic and emits a signal indicating it changing.
        """
        frame = self.frame_blurred_bw

        coord_x, coord_y, width, height = \
            self.eye_rec[0], self.eye_rec[1], self.eye_rec[2], self.eye_rec[3]
        # i is the threshold value used to make the binary image.
        # It is increased until a pupil is found.
        for i in range(45, 90, 2):
            _, thresh = cv2.threshold(frame, i, 250, cv2.THRESH_BINARY)
            # Erode and dilate functions make the pupil
            # a single blob in the thresholded binary image.
            thresh = cv2.erode(thresh, np.ones((5, 5), np.uint8), iterations=4)
            thresh = cv2.dilate(thresh, np.ones((5, 5), np.uint8), iterations=2)

            # Qt image requiers a c-contiguous array
            self.pupil_pic = np.ascontiguousarray(\
                thresh[coord_y:(coord_y+height), coord_x:(coord_x+width)])
            #self.pupilChanged.emit()

            contours, _ = cv2.findContours(\
                thresh[coord_y:(coord_y+height), coord_x:(coord_x+width)], \
                cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            large_blob = contours[0]
            max_area = 0

            # Find the largest blob in the binary image.
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area == cv2.contourArea(contours[len(contours)-1]):
                    break
                if area > max_area:
                    max_area = area
                    large_blob = cnt
                # If only one contour is found no pupil is detected.
                if len(contours) > 1:
                    center = cv2.moments(large_blob)
                if center['m00'] != 0.0:
                    center_coord_x, center_coord_y = \
                        int(center['m10']/center['m00']), int(center['m01']/center['m00'])
                    self.pupil = (coord_x+center_coord_x, coord_y+center_coord_y)
                    break

    def calibrate(self):
        """Calibrate looking forward

        Set zero point, meaning in what position pupil is assumed to be
        facing directly forward to self.center
        """
        self.take_snapshot()
        self.track_pupil()
        self.center = self.pupil

    def draw(self):
        """Create image with descripting text and graphics.
        
        Overlay text and graphic elements to indicate detected pupil
        location, calibrated center line, and whether the eye is
        currently blinking or not.

        Updates the resulting picture to self.result_pic and emit a
        signal to signify it.
        """
        frame = self.frame
        if self.blink:
            string = "BLINK"
        else:
            cv2.circle(frame, (int(self.pupil[0]), int(self.pupil[1])), int(10), (0, 0, 255), 2)
            string = str(self.pupil[0]-self.center[0])
        coord_x, coord_y = self.eye_rec[0], self.eye_rec[1]

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, string, (coord_x, coord_y), font, 1, (255, 255, 255), 2)
        cv2.line(
            frame, \
            (self.center[0], self.center[1]-100), \
            (self.center[0], self.center[1]+100), \
            (255, 0, 0), 5)
        self.result_pic = frame
        #self.resultChanged.emit()
