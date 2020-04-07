"""Module to create BLE connection with DBus api."""

import time
import re

import pydbus
import gi.repository

from PySide2.QtCore import Slot, Signal, QObject

class BluezDBus(QObject):
    """Class to manage bluetooth connection to wheelchair."""
    connection_status = Signal(bool)

    def __init__(self, bt_adapter, bt_address, bt_uuid):
        super().__init__()
        self.bt_adapter = bt_adapter
        self.bt_address = bt_address
        self.uuid = bt_uuid

        self.system_bus = pydbus.SystemBus()
        self.bluez = self.system_bus.get("org.bluez", "/")
        self.managed_objects = self.bluez.GetManagedObjects()
        self.dbus_base = "/org/bluez"

        self.dbus_adapter = self.dbus_base + "/" + self.bt_adapter
        self.hci0 = self.system_bus.get("org.bluez", self.dbus_adapter)

        # Get device object later when it has been found.
        self.dbus_device = self.dbus_adapter + "/dev_" \
            + self.bt_address.replace(":", "_")
        self.device = None

        # Find characteristic and get its dbus object later when connected
        self.dbus_characteristic = None
        self.characteristic = None

        self.dev_pattern = re.compile("/org/bluez/hci0/dev_*")
        self.bt_devices = list(
            filter(
                self.dev_pattern.match,
                self.managed_objects.keys()
            ))

        self.connected = False

    def __del__(self):
        """Disconnect wheelchair when closing program.

        TODO: Delete extra dbus objects, too?
        """
        self.bt_disconnect()

    def _get_characteristic_by_uuid(self):
        """Get BLE characteristic's DBus location."""
        uuid = self.uuid.lower()
        for key in self.managed_objects:
            if key.startswith(self.dbus_device):
                dbus_object = self.system_bus.get("org.bluez", key)
                try:
                    if dbus_object.UUID == uuid:
                        return key
                except AttributeError:
                    pass

    def _set_device(self):
        """Set DBus address for wheelchair's BLE device."""
        self.dbus_device = self.dbus_adapter \
            + "/dev_" \
            + self.bt_address.replace(":", "_")
        self.device = self.system_bus.get("org.bluez", self.dbus_device)

    def _set_characteristic(self):
        """Set DBus address for wheelchair's BLE characteristic."""
        self.dbus_characteristic = self._get_characteristic_by_uuid()
        self.characteristic = self.system_bus.get(
            "org.bluez",
            self.dbus_characteristic)

    @Slot()
    def bt_connect(self):
        """Establish connection with wheelchair."""
        self._find_wheelchair()
        self._set_device()
        self._connect_wheelchair()
        self.connected = True
        self._set_characteristic()
        self.connection_status.emit(self.connected)

    @Slot()
    def bt_disconnect(self):
        """Disconnect wheelchair."""
        self.device.Disconnect()
        self.connected = False
        self.connection_status.emit(self.connected)

    def _find_wheelchair(self):
        """Search for wheelchair with BLE scan."""
        while self.dbus_device not in self.bt_devices:
            self.hci0.StartDiscovery()
            time.sleep(10)
            self.hci0.StopDiscovery()
            self.managed_objects = self.bluez.GetManagedObjects()
            self.bt_devices = list(
                filter(
                    self.dev_pattern.match,
                    self.managed_objects.keys()
                ))

    def _connect_wheelchair(self):
        """Establish bt connection with wheelchair.

        TODO: Improve error handling. Currently only ignores them.
        https://pygobject.readthedocs.io/en/latest/guide/api/error_handling.html
        Errors to handle:
        Connecting fails after timeout:
            g-io-error-quark: GDBus.Error:org.bluez.Error.Failed: \
                Software caused connection abort (36)
        Trying to connect again while already trying to connect:
            g-io-error-quark: GDBus.Error:org.bluez.Error.Failed: \
                Operation already in progress (36)
        """
        while True:
            try:
                self.device.Connect()
                break
            except gi.repository.GLib.Error:
                pass

    @Slot()
    def write_characteristic(self, cmd):
        """Write movement command to wheelchair.

        TODO: Improve exception handling.
        Errors to handle:
        If connection is broken (try to reconnect or do what?):
            g-io-error-quark: GDBus.Error:org.bluez.Error.Failed: \
                Not connected (36)
        """
        if not self.connected:
            return
        try:
            self.characteristic.WriteValue(cmd, {})
        except gi.repository.GLib.Error:
            pass