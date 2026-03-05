from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget, QPushButton, QLabel, QStyle
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon

class SidebarButton(QPushButton):
    def __init__(self, text, icon=None):
        super().__init__()
        self.setText(text)
        if icon:
            self.setIcon(QIcon(icon))
        self.setCheckable(True)
        self.setMaximumHeight(50)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sidebar_expanded = False
        self.current_button = None
        # holder for animation so it doesn't get garbage-collected
        self._sidebar_anim = None
        
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Sidebar Navigation")
        self.setGeometry(100, 100, 1000, 600)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = QWidget()
        self.sidebar.setMaximumWidth(50)
        self.sidebar.setMinimumWidth(50)
        self.sidebar.setStyleSheet("background-color: #2c3e50;")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Create sidebar buttons
        self.buttons = []
        tab_names = ["Home", "Settings", "About", "Help"]
        # choose standard style icons for collapsed view
        icon_map = {
            "Home": self.style().standardIcon(QStyle.SP_DirHomeIcon),
            "Settings": self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            "About": self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            "Help": self.style().standardIcon(QStyle.SP_DialogHelpButton),
        }
        for i, name in enumerate(tab_names):
            icon = icon_map.get(name, QIcon())
            btn = SidebarButton(name, icon)
            # store original label for later when expanding/collapsing
            btn.original_text = name
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    font-weight: bold;
                    font-size: 18px;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:checked {
                    background-color: #3498db;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self.onButtonClicked(idx))
            sidebar_layout.addWidget(btn)
            self.buttons.append(btn)
        
        sidebar_layout.addStretch()
        
        # Create content area with stacked widget
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        for i, name in enumerate(tab_names):
            page = QLabel(f"This is {name} page")
            page.setAlignment(Qt.AlignCenter)
            page.setStyleSheet("font-size: 18px;")
            self.stacked_widget.addWidget(page)
        
        # Add sidebar and stacked widget to main layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stacked_widget,1)
        
        # Set first button as active
        self.buttons[0].setChecked(True)
        self.current_button = self.buttons[0]

        # initially collapsed: hide text
        if not self.sidebar_expanded:
            for btn in self.buttons:
                btn.setText("")
    
    def onButtonClicked(self, index):
        button = self.buttons[index]
        
        if self.current_button == button:
            self.toggleSidebar()
            self.current_button.setChecked(True)      #确保选中状态
        else:
            if self.current_button:
                self.current_button.setChecked(False)
            
            button.setChecked(True)
            self.current_button = button
            self.stacked_widget.setCurrentIndex(index)
    
    def toggleSidebar(self):
        if self.sidebar_expanded:
            self.collapseSidebar()
        else:
            self.expandSidebar()
    
    def expandSidebar(self):
        # ensure minimum width doesn't block animation
        self.sidebar.setMinimumWidth(50)
        self.animateSidebar(self.sidebar.width(), 200)
        self.sidebar_expanded = True
        
        # Update button text visibility
        for btn in self.buttons:
            btn.setText(btn.original_text)

    def collapseSidebar(self):
        # allow shrinking by resetting minimum width
        self.sidebar.setMinimumWidth(0)
        self.animateSidebar(self.sidebar.width(), 50)
        self.sidebar_expanded = False
        for btn in self.buttons:
            btn.setText("")
    
    def animateSidebar(self, start_width, end_width):
        anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        anim.setDuration(400)
        anim.setStartValue(start_width)
        anim.setEndValue(end_width)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        # update minimum width at end to keep layout stable
        # def on_finished():
        #     self.sidebar.setMinimumWidth(end_width)
        # anim.finished.connect(on_finished)
        anim.start()
        self._sidebar_anim = anim