"""Module for dummy wheelchair interface.

Prints sent commands to command line
instead of sending them over bluetooth to receiver.
"""
import time
from wheelchair_base import WheelchairController

class WheelchairDummy(WheelchairController):
    """Dummy wheelchair controller.

    Prints out commands which a real controller would send.
    """
    name = 'Dummy wheelchair'

    def __str__(self):
        return 'Dummy wheelchair'

    def connect_chair(self):
        self.set_connection_status(True)

    def disconnect_chair(self):
        self.set_connection_status(False)

    def write(self):
        """
        Sends command to wheelchair if at least 20ms has passed from
        last command sent. Uses similar non-idealities that a real
        controller would have.

        Parameters:
            None

        Returns:
            boolean: True if the command was written. False if the command was not sent
                because too little time has passed since previous command
        """
        command_delay_ms = 20
        diff = int(time.monotonic()*1000) - self.prev_write
        if diff > command_delay_ms:
            self.prev_write = int(time.monotonic()*1000)
            cmd = [self.drive, self.turn]

            #print('emitting changed')
            self.command_changed.emit(self.drive, self.turn)

            # setting to neutral if no new command is received
            self.drive = self.neutral
            self.turn = self.neutral

            print('Write, value: ', cmd)
            return True
        return False
