"""Main window for wheelchair controller user interface.

Connection adapters and controllers are added to the program here.

Current connection adapters include a dummy for testing which prints
sent commands to terminal, and a Bluetooth LE -based connection

Current controllers include a simple test controller used with
arrow keys, and one which uses camera to track eye movements to
create movement control signals.
"""

from PySide2.QtWidgets import QWidget, QMainWindow, QHBoxLayout, \
    QVBoxLayout, QComboBox
from PySide2.QtCore import Slot

from widget_wheelchair import WheelchairWidget

from wheelchair_dummy import WheelchairDummy
from wheelchair_bt import WheelchairBluetooth
from controller_keyboard import KeyboardController
from controller_eyetrack import EyeTrackerController
from controller_accelerometer import AccelerometerController

class MainWindow(QMainWindow):
    """Main window for wheelchair controller UI.

    The window includes visualization of wheelchair driving commands sent,
    menu for selecting connection adapter, toggles for connecting and
    enabling movements, menu for selecting controller, and space for
    visualizing controller functionality.
    """

    def __init__(self):
        super().__init__()
        self.wheelchair = None
        self.controller = None

        # Choose wheelchair controller from one of these
        self.wheelchairs = []
        self.wheelchairs.append(WheelchairDummy())
        self.wheelchairs.append(WheelchairBluetooth())
        self.wheelchair = self.wheelchairs[0]
        self.wheelchair_widget = WheelchairWidget(self.wheelchair)

        # Choose controller from one of these
        self.controllers = []
        self.controllers.append(KeyboardController)
        self.controllers.append(EyeTrackerController)
        self.controllers.append(AccelerometerController)

        self.controller = self.controllers[0](self.wheelchair)

        self.setWindowTitle('En jaksa kävellä')

        widget = QWidget(self)

        self.setCentralWidget(widget)

        self.wheelchair_chooser = QComboBox()
        for i in self.wheelchairs:
            self.wheelchair_chooser.addItem(i.name)
        self.wheelchair_chooser.activated.connect(self.set_wheelchair)

        self.controller_chooser = QComboBox()
        for i in self.controllers:
            self.controller_chooser.addItem(i.name)
        self.controller_chooser.activated.connect(self.set_controller)

        self.wheelchair_chooser.setFixedSize(250, 24)
        self.controller_chooser.setFixedSize(250, 24)

        self.sub_layout = QVBoxLayout()
        self.sub_layout.addWidget(self.wheelchair_widget)
        self.sub_layout.addWidget(self.wheelchair_chooser)
        self.sub_layout.addWidget(self.controller_chooser)

        self.controller.setFixedSize(900, 550)

        self.layout = QHBoxLayout(widget)
        self.layout.addLayout(self.sub_layout)
        self.layout.addWidget(self.controller)

        self.setLayout(self.layout)

    @Slot(int)
    def set_wheelchair(self, num):
        """Change wheelchair connection adapter.

        When adapter is changed, reset controller to the simple
        keyboard-based controller.

        Arguments:
        num -- Index of wheelchair adapter selected.
        """
        self.wheelchair_chooser.clearFocus()
        self.wheelchair = self.wheelchairs[num]
        widget = WheelchairWidget(self.wheelchair)
        self.sub_layout.replaceWidget(self.wheelchair_widget, widget)
        self.wheelchair_widget.deleteLater()
        self.wheelchair_widget = widget
        self.controller.set_chair(self.wheelchair)

        self.controller_chooser.setCurrentIndex(0)
        self.controller_chooser.activated.emit(0)

    @Slot(int)
    def set_controller(self, num):
        """Change wheelchair controller.

        Arguments:
        num -- Index of wheelchair controller selected.
        """
        self.controller_chooser.clearFocus()
        controller = self.controllers[num](self.wheelchair)
        self.layout.replaceWidget(self.controller, controller)
        self.controller.deleteLater()
        self.controller = controller
