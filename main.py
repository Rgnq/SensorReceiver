import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet


from MainWindow import MainWindow

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_amber.xml',invert_secondary=False)
    w = MainWindow()
    w.SettingsPage.styleSignal.connect(lambda x:apply_stylesheet(app,theme=x))
    w.show()
    app.exec()


if __name__ == "__main__":
    main()