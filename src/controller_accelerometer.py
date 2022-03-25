"""Use accelerometer to control the wheelchair

This simple driver translates accelerometer data to
driving commands.
"""

from PySide2.QtWidgets import QWidget

from Phidget22.Phidget import *
from Phidget22.Devices.Accelerometer import *

class AccelerometerController(QWidget):
    """Use accelerometer data to control the wheelchair

    """
    name = 'Accelerometer glasses'
    def __init__(self, wheelchair):
        super().__init__()
        self.wheelchair = wheelchair
        #self.init_ui()

        accelerometer0 = Accelerometer()
        accelerometer0.openWaitForAttachment(5000)
        accelerometer0.setDataInterval(50)
        accelerometer0.setOnAccelerationChangeHandler(self.write_command)

    def init_ui(self):
        """Initialize the user interface.
        
        """

    def set_chair(self, wheelchair):
        """Set wheelchair adapter where commands are sent.
        
        Arguments:
        wheelchair -- Wheelchair adapter currently in use.
        """
        self.wheelchair = wheelchair


    def write_command(self, accelerometer_obj, acceleration, timestamp):
        """Translate accelerometer data to driving commads.

        Run whenever the accelerometer sends new data. If the
        accelerometer tilt is too small, count is as zero to
        prevent unwanted movements.

        Arguments:
        acceleration -- Acceleration data. 1.0 means 1g (float)
        
        """
        #print("Acceleration: \t"+ str(acceleration[0])+ "  |  "+ str(acceleration[1])+ "  |  "+ str(acceleration[2]))
        #print("Timestamp: " + str(timestamp))
        #print("----------")

        cmd = [self.wheelchair.neutral, self.wheelchair.neutral]

        x = acceleration[0] # <0 backwards  | >0 forward
        y = acceleration[1]
        z = acceleration[2] # <0 left       | >0 rightward

        cmd[0] = int(127*acceleration[0])

        if abs(cmd[0]) < 50:
            cmd[0] = 0

        cmd[1] = int(127*acceleration[2])

        if abs(cmd[1]) < 50:
            cmd[1] = 0


        self.wheelchair.write_command(cmd[0], cmd[1])
