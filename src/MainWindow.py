
from PySide6.QtWidgets import QMainWindow, QWidget, QStackedWidget, QSizePolicy, QHBoxLayout, QVBoxLayout, QSpacerItem , QStyle
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor
from Sidebar import Sidebar
from Menubar import Menubar
from Pages import Homepage, HistoryPage, SettingsPage, AnalysisPage, LogPage

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

        self.sidebar.clickedSignal.connect(self.on_sidebar_button_clicked)
        self.Homepage.sendSignal.connect(self.sendText)
        self.Homepage.right_vertical.serDataSignal.connect(self.LogPage.append_log)
        self.Homepage.right_vertical.serLogSignal.connect(self.LogPage.append_log)
    
    def initUI(self):
        self.initPages()

        # 创建无边框窗口
        self.setWindowTitle("Sensor Receiver")
        self.setGeometry(100, 100, 1200, 900)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
                * {
                    font-family: 'Microsoft Yahei';
                    border-radius: 14px;
                }
                """)
        
        # 创建最顶层布局
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        main_layout = QVBoxLayout(centralWidget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        # 创建菜单栏
        self.menubar = Menubar(self)
        main_layout.addWidget(self.menubar)

        # 创建内容区域布局
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addSpacerItem(QSpacerItem(50, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)) #使页面与侧边栏保持一定距离
        main_layout.addWidget(content_widget)

        # 创建侧边栏
        self.sidebar = Sidebar()
        for name in self.pages_names:
            self.sidebar.add_button(name, icon=self.pages_icons[name])
        self.sidebar.setParent(centralWidget)  # 将侧边栏设置为顶层布局的子组件
        self.sidebar.raise_()  # 确保侧边栏在最上方
        self.setSidebarGeometry() # 设置侧边栏位置和大小
        self.menubar.title.setText(self.pages_names[0])  # 设置初始标题
        
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        # 创建页面并添加到堆叠窗口
        for i, name in enumerate(self.pages_names):
            page = self.pages[name]
            self.stacked_widget.addWidget(page)
        content_layout.addWidget(self.stacked_widget,1)

    def initPages(self):
        self.pages_names = ["实时数据", "历史记录","设置", "数据分析", "日志"]
        self.pages_icons = {
            "实时数据": self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            "历史记录": self.style().standardIcon(QStyle.SP_DirHomeIcon),
            "设置": self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            "数据分析": self.style().standardIcon(QStyle.SP_ComputerIcon),
            "日志": self.style().standardIcon(QStyle.SP_TrashIcon)
        }
        self.Homepage = Homepage()
        self.HistoryPage = HistoryPage()
        self.SettingsPage = SettingsPage()
        self.AnalysisPage = AnalysisPage()
        self.LogPage = LogPage()
        self.pages = {
            "实时数据": self.Homepage,
            "历史记录": self.HistoryPage,
            "设置": self.SettingsPage,
            "数据分析": self.AnalysisPage,
            "日志": self.LogPage
        }

    def setSidebarGeometry(self):
        menubar_h = self.menubar.height()
        self.sidebar.setGeometry(0, menubar_h, self.sidebar.width(), self.height() - menubar_h)

    def on_sidebar_button_clicked(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.menubar.title.setText(self.sidebar.buttons[index].original_text)

    def sendText(self,text):
        #未完成
        self.LogPage.append_log(text)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSidebarGeometry()

    def closeEvent(self, event):
        super().closeEvent(event)
        if self.menubar.timer.isActive():
            self.menubar.timer.stop()
        if self.Homepage.right_vertical.serState:
            self.Homepage.right_vertical.stopSerialThread()
        