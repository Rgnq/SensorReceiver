import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QHBoxLayout, QWidget
from PySide6.QtCore import Qt, QPoint, QRect
from PySide6.QtGui import QCursor
import ctypes

# 获取 Windows 原生最大化/最小化等功能
user32 = ctypes.windll.user32
SWP_NOZORDER = 0x4
SWP_NOACTIVATE = 0x10

class Windows11FramelessWindow(QMainWindow):
    EDGE_MARGIN = 5
    TITLE_HEIGHT = 35  # 模拟标题栏高度

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMouseTracking(True)
        self._resizing = False
        self._drag_pos = None
        self._resize_dir = None
        self._is_maximized = False
        self._restore_geom = self.geometry()

        # ---- 标题栏 ----
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(self.TITLE_HEIGHT)
        self.title_bar.setStyleSheet("background-color: #1e1e2f;")

        self.title_label = QLabel("Windows11 仿原生窗口", self.title_bar)
        self.title_label.setStyleSheet("color: white; margin-left: 10px;")
        self.title_label.setGeometry(10, 0, 300, self.TITLE_HEIGHT)

        # 最小化/最大化/关闭按钮
        self.btn_min = QPushButton("-", self.title_bar)
        self.btn_max = QPushButton("□", self.title_bar)
        self.btn_close = QPushButton("×", self.title_bar)
        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.setFixedSize(40, self.TITLE_HEIGHT)
            btn.setStyleSheet("""
                QPushButton { background-color: transparent; color: white; border: none; }
                QPushButton:hover { background-color: #505050; }
            """)
        self.btn_close.move(460, 0)
        self.btn_max.move(420, 0)
        self.btn_min.move(380, 0)

        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggleMaxRestore)
        self.btn_close.clicked.connect(self.close)

        # 示例内容
        self.content = QLabel("拖动标题栏移动窗口\n拖动边缘调整窗口大小", self)
        self.content.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        self.title_bar.setGeometry(0, 0, self.width(), self.TITLE_HEIGHT)
        self.content.setGeometry(0, self.TITLE_HEIGHT, self.width(), self.height() - self.TITLE_HEIGHT)
        self.btn_close.move(self.width() - 40, 0)
        self.btn_max.move(self.width() - 80, 0)
        self.btn_min.move(self.width() - 120, 0)
        super().resizeEvent(event)

    def toggleMaxRestore(self):
        if self._is_maximized:
            self.setGeometry(self._restore_geom)
            self._is_maximized = False
        else:
            self._restore_geom = self.geometry()
            self.setGeometry(user32.GetSystemMetrics(0), user32.GetSystemMetrics(1),
                             user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
            self._is_maximized = True

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            if self._resize_dir:
                self._resizing = True
            else:
                self._resizing = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._resize_dir = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        global_pos = event.globalPosition().toPoint()
        rect = self.rect()

        # ---- 边缘拖拽判断 ----
        self._resize_dir = None
        if pos.x() < self.EDGE_MARGIN and pos.y() < self.EDGE_MARGIN:
            self.setCursor(Qt.SizeFDiagCursor)
            self._resize_dir = "top_left"
        elif pos.x() > rect.width() - self.EDGE_MARGIN and pos.y() < self.EDGE_MARGIN:
            self.setCursor(Qt.SizeBDiagCursor)
            self._resize_dir = "top_right"
        elif pos.x() < self.EDGE_MARGIN and pos.y() > rect.height() - self.EDGE_MARGIN:
            self.setCursor(Qt.SizeBDiagCursor)
            self._resize_dir = "bottom_left"
        elif pos.x() > rect.width() - self.EDGE_MARGIN and pos.y() > rect.height() - self.EDGE_MARGIN:
            self.setCursor(Qt.SizeFDiagCursor)
            self._resize_dir = "bottom_right"
        elif pos.x() < self.EDGE_MARGIN:
            self.setCursor(Qt.SizeHorCursor)
            self._resize_dir = "left"
        elif pos.x() > rect.width() - self.EDGE_MARGIN:
            self.setCursor(Qt.SizeHorCursor)
            self._resize_dir = "right"
        elif pos.y() < self.EDGE_MARGIN:
            self.setCursor(Qt.SizeVerCursor)
            self._resize_dir = "top"
        elif pos.y() > rect.height() - self.EDGE_MARGIN:
            self.setCursor(Qt.SizeVerCursor)
            self._resize_dir = "bottom"
        else:
            self.setCursor(Qt.ArrowCursor)
            self._resize_dir = None

        # ---- 调整大小 ----
        if self._resizing:
            delta = global_pos - self._drag_pos
            geom = self.geometry()
            if "left" in self._resize_dir:
                geom.setLeft(geom.left() + delta.x())
            if "right" in self._resize_dir:
                geom.setRight(geom.right() + delta.x())
            if "top" in self._resize_dir:
                geom.setTop(geom.top() + delta.y())
            if "bottom" in self._resize_dir:
                geom.setBottom(geom.bottom() + delta.y())
            self.setGeometry(geom)
            self._drag_pos = global_pos

        # ---- 拖动窗口（标题栏） ----
        elif event.buttons() & Qt.LeftButton and pos.y() < self.TITLE_HEIGHT:
            self.move(self.pos() + (global_pos - self._drag_pos))
            self._drag_pos = global_pos

        super().mouseMoveEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.pos().y() < self.TITLE_HEIGHT:
            self.toggleMaxRestore()
        super().mouseDoubleClickEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Windows11FramelessWindow()
    w.resize(500, 400)
    w.show()
    sys.exit(app.exec())