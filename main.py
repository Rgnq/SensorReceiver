import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from colorstyle import *
from i18n import initialize_i18n

from MainWindow import MainWindow

def main():
    # 初始化i18n系统
    initialize_i18n()
    
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_amber.xml',invert_secondary=False)
    w = MainWindow()
    w.SettingsPage.styleSignal.connect(lambda x:switch_theme(app,theme_name=x, MainWindow=w))
    w.SettingsPage.languageChangedSignal.connect(lambda: w.update_ui_text())
    w.show()
    app.exec()

def switch_theme(app, theme_name: str, MainWindow: MainWindow):
    apply_stylesheet(app, theme=theme_name, invert_secondary=False)
    is_dark = theme_name.split('_')[0] == 'dark'
    MainWindow.update_style(is_dark)

if __name__ == "__main__":
    main()