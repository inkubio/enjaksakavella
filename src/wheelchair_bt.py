""" Bluetooth interface to wheelchair

This module implements a BLE connection to wheelchair

NOTE: Hangs UI while establishing bluetooth connection.
      Fix: Put BLE connection to seperate thread.
        Problem: With all threading attemps, only managed
        to get it working if bluetooth library's connect-
        method is called at WheelchairBluetooth's __init__
        method. Same problem appears with Python's threading
        -module, QThread, QRunnable&QThreadPool, and pygatt.
        Pygatt uses pexpect to launch gatttool while bluepy
        uses subprocess, and both hang while creating those
        for gatttool which they are based on.
"""

import time
import json
from bluepy import btle

from wheelchair_base import WheelchairController

class WheelchairBluetooth(WheelchairController):
    """Bluetooth LE adapter for controlling the wheelchair.

    Connects to an Arduino Nano 33 BLE controlling controlling the
    wheelchair.
    
    Address and UUID for the characteristic controlling the wheelchair
    are loaded from config.JSON. Value for neutral command when the
    wheelchair does not move is also loaded from the config file, since
    it depends on physical system connected to wheelchair.
    """

    name = 'Bluetooth wheelchair'

    def __init__(self):
        super().__init__()

        with open('./resources/config_bt.JSON') as config_file:
            config = json.load(config_file)

            self.address = config['address']
            self.uuid = config['characteristic']
            #self.neutral = int(config['neutral'])
            self.neutral = 0

        self.device = btle.Peripheral()
        self.characteristic = None

    def connect_chair(self):
        self.device.connect(self.address)
        self.characteristic = \
            self.device.getCharacteristics(uuid=self.uuid)[0]
        self.set_connection_status(True)

    def disconnect_chair(self):
        self.write_command(self.neutral, self.neutral)
        self.device.disconnect()
        self.set_connection_status(False)

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
            try:
                # ArduinoBLE library requires writes with response wanted.
                self.characteristic.write(bytes(cmd), withResponse=True)
            except btle.BTLEDisconnectError:
                print('Wheelchair has disconnected. Trying to reconnect.')
                self.set_connection_status(False)
                self.connect_chair()
            return True
        return False
