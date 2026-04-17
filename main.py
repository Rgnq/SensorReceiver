import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from colorstyle import *


from MainWindow import MainWindow

def main():
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_amber.xml',invert_secondary=False)
    w = MainWindow()
    w.SettingsPage.styleSignal.connect(lambda x:switch_theme(app,theme_name=x, MainWindow=w))
    w.show()
    app.exec()

def switch_theme(app, theme_name, MainWindow):
    apply_stylesheet(app, theme=theme_name, invert_secondary=False)
    is_dark = theme_name.split('_')[0] == 'dark'
    MainWindow.update_style(is_dark)

if __name__ == "__main__":
    main()