"""Module to use BLE connection on windows.

Stub. Does nothing with bluetooth.
"""

from PySide2.QtCore import Slot, Signal, QObject

from util import ConnectionState

class BLEHelper(QObject):
    connection_status = Signal(ConnectionState)

    def __init__(self, bt_adapter, bt_address, bt_uuid):
        super().__init__()
        self.connected = ConnectionState.DISCONNECTED

    @Slot()
    def bt_connect(self):
        self.connected = ConnectionState.CONNECTED
        self.connection_status.emit(self.connected)

    def bt_disconnect(self):
        self.connected = ConnectionState.DISCONNECTED
        self.connection_status.emit(self.connected)

    def write_characteristic(self, cmd):
        if self.connected == ConnectionState.CONNECTED:
            print(cmd)