"""Base class defining wheelchair adapters

To create a real controller, create a subclass of this class
and implement connect/disconnect and write -methods as needed.

TODO:
    - Gray out drive/turn enable buttons if not connected
"""
#import json
from PySide2.QtCore import QObject, Signal, Slot

from util import ConnectionState

class WheelchairController(QObject):
    """Base class defining wheelchair controller

    To create a real controller, create a subclass of this class
    and implement connect/disconnect and write -methods as needed.
    """
    command_changed = Signal(int, int)
    connection_status_changed = Signal()
    drive_enable_changed = Signal()
    turn_enable_changed = Signal()

    def __init__(self):
        super().__init__()
        self.neutral = 0

        self.drive = self.neutral
        self.turn = self.neutral

        self.enable_drive = False
        self.enable_turn = False

        self.prev_write = 0
        self.connected = ConnectionState.DISCONNECTED

    def __str__(self):
        pass

    @Slot()
    @Slot(bool)
    def set_enable_drive(self, *args):
        """Enable/disable driving wheelchair forward/backward.

        If no argument is given, toggle true/false. Otherwise set the
        given value. Requires connection to wheelchair to work.

        Arguments:
        *args -- Empty if used to toggle value.
        args[0] -- Enable/disable movement forward/backward (bool).
        """
        if self.connected != ConnectionState.CONNECTED:
            return
        if args:
            value = args[0]
        else:
            value = not self.enable_drive

        self.enable_drive = value
        self.drive_enable_changed.emit()

    @Slot()
    @Slot(bool)
    def set_enable_turn(self, *args):
        """Enables/disable turning the wheelchair.

        If no argument is given, toggle true/false. Otherwise set the
        given value.

        Arguments:
        *args -- Empty if used to toggle value.
        args[0] -- Enable/disable turning the wheelchair (bool).
        """
        if self.connected != ConnectionState.CONNECTED:
            return
        if args:
            value = args[0]
        else:
            value = not self.enable_turn
        self.enable_turn = value
        self.turn_enable_changed.emit()

    def connect_chair(self):
        """Establish connection to wheelchair."""
        raise NotImplementedError

    def disconnect_chair(self):
        """Disconnect wheelchair."""
        raise NotImplementedError

    @Slot(bool)
    def set_connection_status(self, status):
        """Set variables to indicate if the wheelchair is connected.
        
        Arguments:
        status -- Connection status.
        """
        self.set_enable_drive(False)
        self.set_enable_turn(False)
        self.connected = status
        self.connection_status_changed.emit()

    def write(self):
        """Send driving command to wheelchair."""
        raise NotImplementedError

    def write_command(self, forward=None, turn=None):
        """Update internal values for sending to wheelchair

        If parameter a parameter is left empty, it is set to neutral
        meaning the wheelchair doesn't move forward/backward or turn

        Arguments:
        forward -- Values outside signed 7-bit will be limited to
            maximum values of signed 7-bit (-127..127) (int).
        turn -- Values outside signed 7-bit will be limited to
            maximum values of signed 7-bit (-127..127). Turn right
            with positive values (int).
        """

        if(forward is None or not self.enable_drive):
            forward = self.neutral
        if(turn is None or not self.enable_turn):
            turn = self.neutral

        self.drive = self._transform_input(forward)
        self.turn = self._transform_input(turn)

        if self.connected == ConnectionState.CONNECTED:
            self.write()

    @staticmethod
    def _transform_input(value):
        """Transforms command inputs to wheelchair's format.
        Transform more intuitive command inputs to wheelchair's format.
        Also limits too large values.

        Arguments:
        value -- Forward or turn value of the wheelchair (int).

        Returns transformed value (int)
        """
        if value > 127:
            value = 127
        elif value < -127:
            value = -127
        if value < 0:
            value = value + 127
        else:
            value = value + 128
        return value
