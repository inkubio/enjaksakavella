"""Qt ui widget for wheelchair controllers."""
from PySide2.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide2.QtGui import QPainter, QColor, QPixmap
from PySide2.QtCore import Slot

NEUTRAL = 127   #112

class DriveBars(QWidget):
    """Draw bars indicating commands sent to wheelchair."""
    def __init__(self, wheelchair):
        super().__init__()
        self.wheelchair = wheelchair

        self.forward = 0
        self.backward = 0
        self.left = 0
        self.right = 0

        #self.wheelchair.command_changed.connect(self.update_bars)

    def paintEvent(self, _):    #event
        painter = QPainter()
        painter.begin(self)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawText(20, 10, 'Movement commands')
        painter.setBrush(QColor(200, 200, 200))
        painter.drawRect(90, 110, 20, -80)
        painter.drawRect(90, 130, 20, 80)
        painter.drawRect(90, 110, -80, 20)
        painter.drawRect(110, 110, 80, 20)
        painter.setBrush(QColor(200, 0, 0))
        painter.drawRect(90, 110, 20, -self.forward*0.8)
        painter.drawRect(90, 130, 20, self.backward*0.8)
        painter.drawRect(90, 110, -self.left*0.8, 20)
        painter.drawRect(110, 110, self.right*0.8, 20)
        painter.end()

    @Slot(int, int)
    def update_bars(self, drive, turn):
        """Calculate new values for drawing bars, and update the bars."""
        self.forward = 100*max((drive-NEUTRAL), 0)/(255-NEUTRAL)
        self.backward = 100*(max((NEUTRAL-drive), 0))/(NEUTRAL)
        self.right = 100*max((turn-NEUTRAL), 0)/(255-NEUTRAL)
        self.left = 100*(max((NEUTRAL-turn), 0))/(NEUTRAL)
        self.update()

    def change_wheelchair(self, wheelchair):
        """Change which wheelchair controller updates the bars."""
        self.wheelchair = wheelchair
        self.wheelchair.command_changed.connect(self.update_bars)

class WheelchairWidget(QWidget):
    """Qt ui widget for controlling and showing information about wheelchair."""
    #s_speed = Signal(bool)
    def __init__(self, wheelchair):
        super().__init__()
        self.wheelchair = None

        self.bars = DriveBars(self.wheelchair)

        self.init_ui()

        self.set_chair(wheelchair)

    def init_ui(self):
        """Build the user interface."""
        self.drive_enable = QPushButton('Enable forward')
        self.drive_enable.setFixedSize(150, 24)
        self.turn_enable = QPushButton('Enable turn')
        self.turn_enable.setFixedSize(150, 24)

        self.enabled = QPixmap('./resources/enabled.png').scaled(24, 24)
        self.disabled = QPixmap('./resources/disabled.png').scaled(24, 24)

        self.drive_label = QLabel()
        self.turn_label = QLabel()
        self.connect_label = QLabel()

        self.drive_label.setPixmap(self.disabled)
        self.turn_label.setPixmap(self.disabled)
        self.connect_label.setPixmap(self.disabled)

        self.connect_button = QPushButton('Connect')
        self.connect_button.setFixedSize(150, 24)

        drive_layout = QHBoxLayout()
        drive_layout.addWidget(self.drive_label)
        drive_layout.addWidget(self.drive_enable)

        turn_layout = QHBoxLayout()
        turn_layout.addWidget(self.turn_label)
        turn_layout.addWidget(self.turn_enable)

        connect_layout = QHBoxLayout()
        connect_layout.addWidget(self.connect_label)
        connect_layout.addWidget(self.connect_button)

        layout = QVBoxLayout()
        layout.addWidget(self.bars)
        layout.addLayout(drive_layout)
        layout.addLayout(turn_layout)
        layout.addLayout(connect_layout)

        self.setLayout(layout)

    @Slot()
    def set_drive(self):
        """Set forward enable/disable button."""
        if self.wheelchair.enable_drive:
            self.drive_enable.setText('Disable forward')
            self.drive_label.setPixmap(self.enabled)
        else:
            self.drive_enable.setText('Enable forward')
            self.drive_label.setPixmap(self.disabled)

    @Slot()
    def set_turn(self):
        """Set turn enable/disable button."""
        if self.wheelchair.enable_turn:
            self.turn_enable.setText('Disable turn')
            self.turn_label.setPixmap(self.enabled)
        else:
            self.turn_enable.setText('Enable turn')
            self.turn_label.setPixmap(self.disabled)

    @Slot()
    def set_connect(self):
        """Set connect button."""
        if self.wheelchair.connected:
            self.connect_label.setPixmap(self.enabled)
            self.connect_button.setText('Disconnect')
        else:
            self.connect_label.setPixmap(self.disabled)
            self.connect_button.setText('Connect')

    @Slot()
    def toggle_connection(self):
        """Connect or disconnect wheelchair based on connection status."""
        if self.wheelchair.connected:
            self.wheelchair.disconnect_chair()
        else:
            self.wheelchair.connect_chair()

    @Slot(int)
    def set_chair(self, wheelchair):
        """Change wheelchair adapter."""
        if self.wheelchair:
            self.wheelchair.disconnect_chair()

        self.wheelchair = wheelchair
        self.bars.change_wheelchair(self.wheelchair)

        #Signals to control wheelchair controller
        self.drive_enable.clicked.connect(self.wheelchair.set_enable_drive)
        self.turn_enable.clicked.connect(self.wheelchair.set_enable_turn)
        self.connect_button.clicked.connect(self.toggle_connection)

        #Signals for updating buttons at this widget
        self.wheelchair.drive_enable_changed.connect(self.set_drive)
        self.wheelchair.turn_enable_changed.connect(self.set_turn)
        self.wheelchair.connection_status_changed.connect(self.set_connect)
