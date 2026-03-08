import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet


from MainWindow import MainWindow

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml',invert_secondary=True)
    w = MainWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    main()