from PySide6.QtCore import Qt, QDateTime, QTimer
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QIcon, QCursor
from colorstyle import *

class Menubar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.old_pos = None
        self.maxstate = False
        self.is_dark_theme = True  # 追踪当前主题
        
        
        self.setFixedHeight(40)
        self.setStyleSheet(get_menubar_stylesheet(self.is_dark_theme))
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # 窗口标题
        self.titleWidget = QWidget()
        self.titleWidget.setLayout(QHBoxLayout())
        self.title = QLabel("")
        self.title.setStyleSheet(get_menubar_title_stylesheet(self.is_dark_theme))
        self.titleTime = QLabel("当前时间：")
        self.titleWidget.layout().addWidget(self.title)
        self.titleWidget.layout().addWidget(self.titleTime)
        #self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # 窗口图标（可选）
        # icon_label = QLabel("")
        # #icon_label.setPixmap(QIcon("app_icon.png").pixmap(20, 20))
        # icon_label.setFixedSize(20, 20)
        
        # 按钮区域
        btn_widget = QWidget()
        btn_layout = QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(8)
        
        self.min_btn = QPushButton("−")
        self.max_btn = QPushButton("□")
        self.close_btn = QPushButton("×")
        
        for btn in (self.min_btn, self.max_btn, self.close_btn):
            btn.setFixedSize(32, 28)
            btn.setStyleSheet(get_menubar_button_stylesheet(self.is_dark_theme))
            btn_layout.addWidget(btn)
        
        self.min_btn.clicked.connect(self.parent.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)
        
        # 布局组合
        #layout.addWidget(icon_label)
        layout.addWidget(self.titleWidget, stretch=1)
        layout.addWidget(btn_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # 每秒更新一次时间
        self.update_time()  # 初始化时立即更新时间显示

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        self.setStyleSheet(get_menubar_stylesheet(is_dark))
        self.title.setStyleSheet(get_menubar_title_stylesheet(is_dark))
        for btn in (self.min_btn, self.max_btn, self.close_btn):
            btn.setStyleSheet(get_menubar_button_stylesheet(is_dark))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.maxstate == False:
            self.old_pos = event.globalPosition().toPoint()
            self.setCursor(QCursor(Qt.SizeAllCursor))
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.parent.move(self.parent.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None
        self.setCursor(QCursor(Qt.ArrowCursor))

    def toggle_maximize(self):
        if self.maxstate:
            self.parent.showNormal()
            self.maxstate = False
            self.max_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.maxstate = True
            self.max_btn.setText("❐")
    
    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        self.titleTime.setText(f"当前时间：{current_time}")