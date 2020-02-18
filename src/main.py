"""Program for controlling an electric wheelchair with custom controllers

This program works as glue between custom controllers and an Arduino
controlling an electric wheelchair. It consists of a graphical user
interface which is used to control connection methods to the Arduino
and different controllers. Visualization of controller output and
commands to the Arduino are also provided.

Written mainly by Tuomas Rantataro.
"""

import sys
from PySide2.QtWidgets import QApplication
from mainwindow import MainWindow

def main():
    """Main program for controlling wheelchair."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
    