"""Controller for rnet_ble module to drive electric wheelchair using eye movements

Written originally for serial connection by Antti Alastalo, modified
for rnet_ble module by Tuomas Rantataro

TODO: Pieces to create:
 - Display feed from camera when selecting
 - Calibration for max left/right eye movements
 - Adjusting camera settings (brightness, contrast, saturation, gain, exposure?)
     https://docs.opencv.org/2.4/modules/highgui/doc/reading_and_writing_images_and_video.html#videocapture-get
 - Do not crash when no camera is found
"""

import time
import statistics

from PySide2.QtCore import Qt, QTimer, Slot
from PySide2.QtWidgets import QWidget, QGridLayout, QLabel, \
  QVBoxLayout, QHBoxLayout, QPushButton, QComboBox
from PySide2.QtGui import QImage, QPixmap

from eyetracker import Eyetracker

class EyeTrackerController(QWidget):
    """A Qt Widget for eye tracking controller's UI

    Creates UI for calibrating eye tracker controller and showing its
    working principle.

    Arguments:
    wheelchair -- Wheelchair adapter currently in use.
    """

    name = 'Eye Tracker'
    def __init__(self, wheelchair):
        super().__init__()
        self.wheelchair = wheelchair
        self.tracker = Eyetracker()

        self.init_ui()

        self.tracker.eyeChanged.connect(self.update_calib_image)

        self.start = time.time()
        self.end = self.start
        self.blinktimer = 0
        self.forwardmode = False

        self.update_timer = QTimer()
        self.update_timer.setInterval(50)
        self.update_timer.timeout.connect(self.next_frame)

        self.dist_min = 9999
        self.dist_max = -9999
        self.dist_old = 0

        self.distances = [0, 0, 0, 0]

        self.rotate = 0

        self.rot_calibrated = False

    def __del__(self):
        if self.tracker.cam:
            self.tracker.cam.release()

    def set_chair(self, wheelchair):
        """Set new wheelchair object

        Change internal wheelchair in case the wheelchair adapter
        is changed.

        Arguments:
        wheelchair -- New wheelchair adapter to use.
        """
        self.wheelchair = wheelchair

    def init_ui(self):
        """Initialize user interface.
        
        Contains buttons for choosing camera andcalibration steps, and
        images visualizing what the adapter is doing. Main picture is
        from the camera with information analyzed from image drawn on
        top of it. Smaller images showing how images processed for
        pupil and blinking detection look like.
        """

        self.main_image = QLabel()
        self.pupil_image = QLabel()
        self.blink_image = QLabel()

        self.main_image.setFixedSize(self.size())

        camera_select = QComboBox()
        for i in self.tracker.cams:
            camera_select.addItem('Camera {}'.format(i))
        #cameraSelect.currentIndexChanged.connect(self.tracker.selectCamera)
        camera_select.activated.connect(self.tracker.select_camera)

        calib_button = QPushButton('Find eye')
        calib_button.clicked.connect(self.find_eye)

        calib_look_button = QPushButton('Calibrate (Look forward)')
        calib_look_button.clicked.connect(self.calibrate_and_start)

        labs = QHBoxLayout()
        labs.addWidget(QLabel('Pupil image'), Qt.AlignBottom)
        labs.addWidget(QLabel('Blink image'), Qt.AlignBottom)

        imgs = QHBoxLayout()
        imgs.addWidget(self.pupil_image)
        imgs.addWidget(self.blink_image)

        calib_layout = QVBoxLayout()
        calib_layout.addWidget(calib_button)
        calib_layout.addWidget(calib_look_button)
        calib_layout.addWidget(camera_select)
        calib_layout.addLayout(labs)
        calib_layout.addLayout(imgs)

        layout = QGridLayout(self)
        layout.addLayout(calib_layout, 0, 0)
        layout.addWidget(self.main_image, 0, 1)
        self.setLayout(layout)

    @Slot()
    def find_eye(self):
        """Find eye location from image

        Stops eye movement detection and tries to find an eye again.

        TODO: Move to another thread. Hangs UI until eye is found.
        """
        self.update_timer.stop()
        self.tracker.get_bounding_rectangle()

    @Slot()
    def calibrate_and_start(self):
        """Start tracking eye movements after calibration.

        Calibrate the user's eye to look forward and after that start
        tracking its movements.
        """
        self.tracker.calibrate()
        self.update_timer.start()

    @Slot()
    def set_max_dirs(self):
        """Calibrate for max eye movement values to left/right."""
        raise NotImplementedError

    @Slot()
    def update_calib_image(self):
        """Get a new image for calibrating eye position.

        Take image of an eye for calibration purpose.
        """
        img = self.tracker.eye_pic
        height, width, channels = img.shape
        convert_to_qt_format = QImage(img.data, width, height, width*channels, QImage.Format_RGB888)
        pm_eye = QPixmap.fromImage(convert_to_qt_format)
        self.main_image.setPixmap(pm_eye)

    def check_blink(self):
        """Detect eye blinking.

        Check if the eye has been blinking for at least 0.5 seconds.
        This is done to make involuntary, always happening eye blinks
        not count as commands.
        """
        blink_threshold_sec = 0.5
        self.end = time.time()
        time_diff = self.end - self.start
        if self.tracker.detect_blink():
            self.blinktimer += time_diff
        else:
            self.blinktimer = 0
        self.start = time.time()

        if self.blinktimer > blink_threshold_sec:
            if self.forwardmode:
                self.forwardmode = False
            else:
                self.forwardmode = True
            self.blinktimer = -9999

    def moving_average(self, new_value):
        """Calculate moving average of 5 previous frames.

        """
        self.distances.pop(0)
        self.distances.append(new_value)
        return statistics.mean(self.distances)

    def drive_wheelchair(self):
        """Set driving command to wheelchair.

        If eye blinking is not detected, send command to wheelchair to
        move in desired way. If eye blink is detected, stop the
        wheelchair. Move left/right according to pupil position only if
        it deviates from calibratet "looking forward" -position 
        """
        self.check_blink()
        if not self.tracker.blink:
            self.tracker.track_pupil()
            dist_new = self.tracker.center[0] - self.tracker.pupil[0]

            dist = self.moving_average(dist_new)

            if not self.rot_calibrated:
                self.dist_min = min(self.dist_min, dist)
                self.dist_max = max(self.dist_max, dist)
                print("min: {} | max: {}".format(self.dist_min, self.dist_max))

            if dist < self.dist_min/2:
                self.rotate = self.rotate - 10*float(dist)/float(self.dist_min)
            elif dist < 0:  # Move towards zero
                self.rotate = min(0, self.rotate + self.dist_min/20)
            if dist > self.dist_max/2:
                self.rotate = self.rotate + 10*float(dist)/float(self.dist_max)
            elif dist > 0:
                self.rotate = max(0, self.rotate - self.dist_max/20)
            if self.forwardmode:
                forward = 127
            else:
                forward = self.wheelchair.neutral

            if self.rotate > 127:
                self.rotate = 127
            if self.rotate < -127:
                self.rotate = -127
            cmd = [forward, int(self.rotate)]
        else:
            cmd = [self.wheelchair.neutral, self.wheelchair.neutral]

        self.wheelchair.write_command(cmd[0], cmd[1])

    def create_images(self):
        """Create images visualizing eye tracker working principle.

        Show image from camera with analyzed pupil movement and blink
        detection values. Also show processed images used for pupil
        movement and blink detection.
        """
        self.tracker.draw()
        img = self.tracker.result_pic
        height, width, channels = img.shape
        bytes_per_line = channels*width
        convert_to_qt_format = QImage(img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pm_result = QPixmap.fromImage(convert_to_qt_format.rgbSwapped())

        img = self.tracker.pupil_pic
        height, width = img.shape
        convert_to_qt_format = QImage(img.data, width, height, width, QImage.Format_Grayscale8)
        pm_pupil = QPixmap.fromImage(convert_to_qt_format)

        img = self.tracker.blink_pic
        height, width = img.shape
        convert_to_qt_format = QImage(img.data, width, height, width, QImage.Format_Grayscale8)
        pm_blink = QPixmap.fromImage(convert_to_qt_format)

        self.main_image.setPixmap(pm_result) #.scaled(680, 400, Qt.KeepAspectRatio))
        self.pupil_image.setPixmap(pm_pupil.scaled(128, 128, Qt.KeepAspectRatio))
        self.blink_image.setPixmap(pm_blink.scaled(128, 128, Qt.KeepAspectRatio))

    @Slot()
    def next_frame(self):
        """Things done for each frame of eye movement detection.

        Run continously when controlling wheelchair.
        """
        self.tracker.take_snapshot()
        self.drive_wheelchair()
        self.create_images()
