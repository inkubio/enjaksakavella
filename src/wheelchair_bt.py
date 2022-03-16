""" Bluetooth interface to wheelchair

This module implements a BLE connection to wheelchair.

TODO:
    - Fix disconnection/connection and enable turn/forward when changing
        wheelchair connection.
"""

import sys
import time
import threading
import json

from wheelchair_base import WheelchairController

if sys.platform.startswith("linux"):
    from bluez_dbus import BLEHelper
elif sys.platform.startswith("win"):
    from win_bt import BLEHelper

class WheelchairBluetooth(WheelchairController):
    """Bluetooth LE adapter for controlling the wheelchair.

    Connects to an Arduino Nano 33 BLE controlling controlling the
    wheelchair.

    Bluetooth adapter name, address and UUID for the characteristic controlling
    the wheelchair are loaded from config.JSON. Value for neutral command when
    the wheelchair does not move is also loaded from the config file, since it
    depends on physical system connected to wheelchair.
    """

    name = "Bluetooth wheelchair"

    def __init__(self):
        super().__init__()

        with open("resources/config_bt.JSON") as config_file:
            config = json.load(config_file)

            self.adapter = config["adapter"]
            self.address = config["address"]
            self.uuid = config["characteristic"]
            #self.neutral = int(config['neutral'])
            self.neutral = 0

        self.bluetooth = BLEHelper(self.adapter, self.address, self.uuid)
        self.bluetooth.setParent(self)

        self.bluetooth.connection_status.connect(self.set_connection_status)

        #self.target = None
        self.t = None

    def __del__(self):
        self.bluetooth.stop_thread = True

    def connect_chair(self):
        self.t = threading.Thread(
            target = self.bluetooth.bt_connect
            )
        self.t.start()

    def disconnect_chair(self):
        threading.Thread(
            target=self.bluetooth.bt_disconnect
            ).start()

    def write(self):
        """Send driving command to wheelchair.

        Send the command only if at least 200ms has passed from last
        command sent. This is done to prevent movement commants getting
        queued up and sent later.

        TODO: Fix to allow shorter time between two commands. Currently
        200ms seems to be the minimum delay between two commands which
        works. If commands are sent with shorter delay between them,
        they will get queued up and sent one after another with ~300ms
        delay between them until the queue is empty.

        Parameters:
        None

        Returns:
        boolean: True if the command was written. False if the command
            was not sent because too little time has passed since
            previous command.
        """
        command_delay_ms = 200
        diff = int(time.monotonic()*1000) - self.prev_write
        if diff > command_delay_ms:
            self.prev_write = int(time.monotonic()*1000)
            cmd = [self.drive, self.turn]

            self.command_changed.emit(self.drive, self.turn)

            self.drive = self.neutral
            self.turn = self.neutral

            self.bluetooth.write_characteristic(cmd)

            return True
        return False
