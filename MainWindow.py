import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QSizePolicy, QHBoxLayout, QVBoxLayout, QSpacerItem , QStyle
from PySide6.QtCore import Qt
from Sidebar import Sidebar
from Menubar import Menubar
from Pages import Homepage, HistoryPage, SettingsPage, AnalysisPage, LogPage

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.initUI()

        self.sidebar.clickedSignal.connect(self.on_sidebar_button_clicked)
    
    def initUI(self):
        self.setWindowTitle("Sensor Receiver")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
                * {
                    font-family: 'Microsoft Yahei';
                    border-radius: 10px;
                }
                """)
        # Create central widget and main layout
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        main_layout = QVBoxLayout(centralWidget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)
        # Create menubar
        self.menubar = Menubar(self)
        main_layout.addWidget(self.menubar)
        # Create content area with horizontal layout
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        main_layout.addWidget(content_widget)
        content_layout.addSpacerItem(QSpacerItem(50, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))  # Add spacer to push content to the left
        

        # Create sidebar
        self.sidebar = Sidebar()
        btn_names = ["实时数据", "历史记录","设置", "数据分析", "日志"]
        btn_icons = {
            "实时数据": self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            "历史记录": self.style().standardIcon(QStyle.SP_DirHomeIcon),
            "设置": self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            "数据分析": self.style().standardIcon(QStyle.SP_ComputerIcon),
            "日志": self.style().standardIcon(QStyle.SP_TrashIcon)
        }
        for name in btn_names:
            self.sidebar.add_button(name, icon=btn_icons[name])
        #content_layout.addWidget(self.sidebar)
        self.sidebar.setParent(centralWidget)  # 将侧边栏设置为内容区域的子组件
        self.sidebar.raise_()  # 确保侧边栏在内容区域之上
        self.setSidebarGeometry() # 设置侧边栏位置和大小
        self.menubar.title.setText(btn_names[0])  # 设置初始标题
        
        # Create content area with stacked widget
        self.stacked_widget = QStackedWidget()
        # Create pages
        self.pages = {
            "实时数据": Homepage(),
            "历史记录": HistoryPage(),
            "设置": SettingsPage(),
            "数据分析": AnalysisPage(),
            "日志": LogPage()  # 占位页，后续可以替换为实际页面
        }
        for i, name in enumerate(btn_names):
            page = self.pages[name]
            self.stacked_widget.addWidget(page)
        content_layout.addWidget(self.stacked_widget,1)

        self.pages["实时数据"].AX_label.setText("AX: --")

    def setSidebarGeometry(self):
        menubar_h = self.menubar.height()
        self.sidebar.setGeometry(0, menubar_h, self.sidebar.width(), self.height() - menubar_h)

    def on_sidebar_button_clicked(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.menubar.title.setText(self.sidebar.buttons[index].original_text)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSidebarGeometry()

    def closeEvent(self, event):
        super().closeEvent(event)
        if self.menubar.timer.isActive():
            self.menubar.timer.stop()
        