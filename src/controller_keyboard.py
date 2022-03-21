"""Simple keyboard using controller.

This controller is for testing purposes to send reliably commands to
the wheelchair.
"""

from PySide2.QtCore import Qt, QTimer
from PySide2.QtGui import QPixmap, QTransform
from PySide2.QtWidgets import QWidget, QLabel, QGridLayout

class KeyboardController(QWidget):
    """Simple keyboard controller for wheelchair.
    
    Use arrow keys to move wheelchair forward/backward and for turning
    left/right. The controller detects multiple keypresses in somewhat
    reliable way. If opposing keys are pressed (left and right or up
    and down) at the same time, does not send command on that axis.
    Keypresses are visualized with a stylished arrow pad with lit
    arrows for keys pressed.
    
    This controller could be much improved but does its job.

    Arguments:
    wheelchair -- Wheelchair adapter currently in use.
    """
    name = 'Keyboard controller'
    def __init__(self, wheelchair):
        super().__init__()
        self.wheelchair = wheelchair
        self.grabKeyboard()
        self.init_ui()
        # Variables for keypresses
        self.first_release = True
        self.keylist = []

        self.release_timer = QTimer()
        self.release_timer.start(50)
        self.release_timer.timeout.connect(self._process_keys)

    def _process_keys(self):
        self.processmultikeys(self.keylist)

    def init_ui(self):
        """Initialize the user interface.
        
        Create stylished arrow pad where the arrow images are lit/unlit
        depending if keys are pressed or not pressed.
        """
        self.forward_label = QLabel()
        self.backward_label = QLabel()
        self.right_label = QLabel()
        self.left_label = QLabel()
        self.rotate_right = QTransform().rotate(90)
        self.rotate_down = QTransform().rotate(180)
        self.rotate_left = QTransform().rotate(270)

        self.arrow1 = QPixmap('./resources/arrow1.png')
        self.arrow2 = QPixmap('./resources/arrow2.png')

        self.forward_label.setPixmap(self.arrow1)
        self.right_label.setPixmap(self.arrow1.transformed(self.rotate_right))
        self.backward_label.setPixmap(self.arrow1.transformed(self.rotate_down))
        self.left_label.setPixmap(self.arrow1.transformed(self.rotate_left))

        # setting layout for arrow key images
        layout = QGridLayout(self)
        layout.addWidget(self.forward_label, 0, 1, Qt.AlignBottom)
        layout.addWidget(self.backward_label, 1, 1)
        layout.addWidget(self.right_label, 1, 2)
        layout.addWidget(self.left_label, 1, 0)
        self.setLayout(layout)

    def set_chair(self, wheelchair):
        """Set wheelchair adapter where commands are sent.
        
        Arguments:
        wheelchair -- Wheelchair adapter currently in use.
        """
        self.wheelchair = wheelchair

    def _get_keyname(self, key):
        if key == Qt.Key.Key_Up:
            return "Up"
        if key == Qt.Key.Key_Down:
            return "Down"
        if key == Qt.Key.Key_Left:
            return "Left"
        if key == Qt.Key.Key_Right:
            return "Right"

    def keyPressEvent(self, event):
        self.keylist.append(event.key())

    def keyReleaseEvent(self, event):
        self.keylist.remove(event.key())

    def processmultikeys(self, keyspressed):
        """Process multiple simultaneous keypresses.
        
        Use keyPressEvent and keyReleaseEvent to fill/empty list
        containing keys pressed. Check that list and send movement
        commands based on which keys are pressed. Also update the
        visualization of which keys are pressed.

        Arguments:

        keyspressed -- List of keys currently pressed.
        """
        cmd = [self.wheelchair.neutral, self.wheelchair.neutral]

        key_up = Qt.Key.Key_Up in keyspressed
        key_down = Qt.Key.Key_Down in keyspressed
        key_left = Qt.Key.Key_Left in keyspressed
        key_right = Qt.Key.Key_Right in keyspressed

        if key_up != key_down:
            if key_up:
                cmd[0] = 127
            else:
                cmd[0] = -127

        if key_left != key_right:
            if key_right:
                cmd[1] = 127
            else:
                cmd[1] = -127

        if key_up:
            self.forward_label.setPixmap(self.arrow2)
        else:
            self.forward_label.setPixmap(self.arrow1)
        if key_down:
            self.backward_label.setPixmap(self.arrow2.transformed(self.rotate_down))
        else:
            self.backward_label.setPixmap(self.arrow1.transformed(self.rotate_down))
        if key_right:
            self.right_label.setPixmap(self.arrow2.transformed(self.rotate_right))
        else:
            self.right_label.setPixmap(self.arrow1.transformed(self.rotate_right))
        if key_left:
            self.left_label.setPixmap(self.arrow2.transformed(self.rotate_left))
        else:
            self.left_label.setPixmap(self.arrow1.transformed(self.rotate_left))

        self.wheelchair.write_command(cmd[0], cmd[1])
