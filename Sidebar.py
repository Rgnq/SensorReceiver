from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon

class SidebarButton(QPushButton):
    def __init__(self, text, icon=None):
        super().__init__()
        self.setText(text)
        if icon:
            self.setIcon(QIcon(icon))
        self.setCheckable(True)
        self.setMaximumHeight(50)

class Sidebar(QWidget):
    clickedSignal = Signal(int)

    def __init__(self, parent=None):
        super().__init__()
        # Create sidebar buttons
        self.buttons = []
        self.selected_index = -1
        self._sidebar_anim = None
        self.sidebar_expanded = False
        self.collapsed_width = 50
        self.expanded_width = 200
        

        self.initUI()


        
    def initUI(self):
        self.setFixedWidth(self.collapsed_width)
        #self.setStyleSheet("background-color: #2c3e50;")
        self.setStyleSheet("background-color: rgba(50, 63, 80, 80);")
        self.setAttribute(Qt.WA_StyledBackground, True)   # 绘制背景色
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 10, 0, 0)
        self.layout.setSpacing(2)

        self.layout.addStretch()  # Add stretch to push buttons to the top

        
    
    def add_button(self, name, icon=None):
        if not self.sidebar_expanded:
            button = SidebarButton("", icon=icon)
        else:
            button = SidebarButton(name, icon=icon)
        button.setStyleSheet("""
                SidebarButton {
                    background-color: #2c3e50;
                    color: white;
                    border: none;
                    font-weight: bold;
                    font-size: 18px;
                    text-align: center;
                    icon-size: 30px;
                }
                SidebarButton:hover {
                    background-color: #34495e;
                }
                SidebarButton:checked {
                    background-color: #3498db;
                }
            """)
        button.setCheckable(True)
        button.setMaximumHeight(100)
        if not self.buttons:
            button.setChecked(True)
            self.selected_index = 0
        button.original_text = name
        self.buttons.append(button)
        # 插入到 stretch 前一位（也就是所有按钮的最后面，stretch 永远在最底）
        # len(self.buttons)-1 是当前新按钮的索引
        self.layout.insertWidget(len(self.buttons) - 1, button)
        # 单选互斥
        button.clicked.connect(lambda checked, idx=len(self.buttons)-1: self._on_button_clicked(idx))

    def _on_button_clicked(self, index):
        if self.selected_index == index:
            self.toggleSidebar()
            self.buttons[index].setChecked(True)  # 保持当前按钮选中状态
        else:
            if self.selected_index != -1:
                self.buttons[self.selected_index].setChecked(False)
            self.selected_index = index
        self.clickedSignal.emit(index)

    def toggleSidebar(self):
        if self.sidebar_expanded:
            self.collapseSidebar()
        else:
            self.expandSidebar()
    
    def expandSidebar(self):
        # ensure minimum width doesn't block animation
        #self.setMaximumWidth(self.width())
        self.sidebar_expanded = True
        #print(self.minimumWidth(),self.maximumWidth())
        self.setMaximumWidth(self.expanded_width)  # 设置最大宽度以允许扩展
        self.animateSidebar(self.width(), self.expanded_width, b"minimumWidth")  
        # Update button text visibility
        # for btn in self.buttons:
        #     btn.setText(btn.original_text)

    def collapseSidebar(self):
        # allow shrinking by resetting maximum width
        #self.setMaximumWidth(self.width())
        self.sidebar_expanded = False
        #print(self.minimumWidth(),self.maximumWidth())
        self.setMinimumWidth(self.collapsed_width)  # 设置最小宽度以允许收缩   
        self.animateSidebar(self.width(), self.collapsed_width, b"maximumWidth")     
        # for btn in self.buttons:
        #     btn.setText("")
    
    def animateSidebar(self, start_width, end_width, property_name=b"minimumWidth"):
        if self._sidebar_anim and self._sidebar_anim.state() == QPropertyAnimation.Running:
            self._sidebar_anim.stop()
        anim = QPropertyAnimation(self, property_name)
        anim.setDuration(200)
        anim.setStartValue(start_width)
        anim.setEndValue(end_width)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        # update minimum width at end to keep layout stable
        # def on_finished():
        #     self.sidebar.setMinimumWidth(end_width)
        anim.finished.connect(lambda: [btn.setText(btn.original_text if self.sidebar_expanded else "") for btn in self.buttons])
        #anim.finished.connect(lambda: print(self.minimumWidth(),self.maximumWidth()))
        anim.start()
        self._sidebar_anim = anim
