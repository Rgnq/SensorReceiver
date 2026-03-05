
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
        self.pages["实时数据"].sendSignal.connect(self.sendText)
    
    def initUI(self):
        # 创建无边框窗口
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
        pages_names = ["实时数据", "历史记录","设置", "数据分析", "日志"]
        pages_icons = {
            "实时数据": self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            "历史记录": self.style().standardIcon(QStyle.SP_DirHomeIcon),
            "设置": self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            "数据分析": self.style().standardIcon(QStyle.SP_ComputerIcon),
            "日志": self.style().standardIcon(QStyle.SP_TrashIcon)
        }
        for name in pages_names:
            self.sidebar.add_button(name, icon=pages_icons[name])
        self.sidebar.setParent(centralWidget)  # 将侧边栏设置为顶层布局的子组件
        self.sidebar.raise_()  # 确保侧边栏在最上方
        self.setSidebarGeometry() # 设置侧边栏位置和大小
        self.menubar.title.setText(pages_names[0])  # 设置初始标题
        
        # 创建堆叠窗口
        self.stacked_widget = QStackedWidget()
        # 创建页面并添加到堆叠窗口
        self.pages = {
            "实时数据": Homepage(),
            "历史记录": HistoryPage(),
            "设置": SettingsPage(),
            "数据分析": AnalysisPage(),
            "日志": LogPage()
        }
        for i, name in enumerate(pages_names):
            page = self.pages[name]
            self.stacked_widget.addWidget(page)
        content_layout.addWidget(self.stacked_widget,1)


    def setSidebarGeometry(self):
        menubar_h = self.menubar.height()
        self.sidebar.setGeometry(0, menubar_h, self.sidebar.width(), self.height() - menubar_h)

    def on_sidebar_button_clicked(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.menubar.title.setText(self.sidebar.buttons[index].original_text)

    def sendText(self,text):
        #未完成
        self.pages["日志"].append_log(text)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setSidebarGeometry()

    def closeEvent(self, event):
        super().closeEvent(event)
        if self.menubar.timer.isActive():
            self.menubar.timer.stop()
        