import sys
from PySide6.QtWidgets import QApplication


from MainWindow import MainWindow
from qt_material import apply_stylesheet



if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml',invert_secondary=True)
    w = MainWindow()
    #w.setStyleSheet("* {font-family: 'Microsoft Yahei';}")
    # with open("style.qss", "w") as f:
    #     f.write(w.menubar.max_btn.styleSheet())
    w.show()
    app.exec()