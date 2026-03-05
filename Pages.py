from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QSpacerItem,
                            QSizePolicy, QGridLayout, QComboBox, QPushButton, QLineEdit, QTextEdit, QCheckBox)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal
from serial.tools import list_ports
from Serial import SerialThread


class Homepage(QWidget):
    sendSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.AX_label = QLabel("......")
        self.AY_label = QLabel("......")
        self.AZ_label = QLabel("......")
        self.GX_label = QLabel("......")
        self.GY_label = QLabel("......")
        self.GZ_label = QLabel("......")
        self.CO2_label = QLabel("......")
        self.TVOC_label = QLabel("......")
        self.TEMP_label = QLabel("......")
        self.HUM_label = QLabel("......")
        self.PRESS_label = QLabel("......")

        self.labels = [self.AX_label, self.AY_label, self.AZ_label, self.GX_label, self.GY_label, self.GZ_label,
                        self.CO2_label, self.TVOC_label,
                        self.TEMP_label, self.HUM_label, self.PRESS_label]
        
        for label in self.labels:
            label.setStyleSheet("background-color: rgba(80,80,80,100)")

        self.anim = None  # 用于存储动画对象
        self.settingExpanded = False  # 记录设置面板的展开状态

        self.initUI()

        self.setStyleSheet('''
                        QLabel[text~="MPU6050"], QLabel[text~="气体传感器"], QLabel[text~="温湿压传感器"]
                        {background-color: #404040}
                    ''')
    
    def initUI(self):
        # 外层布局
        self.main_horizontal = QHBoxLayout(self)
        self.main_horizontal.setObjectName("main_horizontal")

        # 左侧监测部分
        self.left_content = QVBoxLayout()
        self.left_content.setObjectName("left_content")
        # 左侧监测部分--上方三块传感器数据区域
        self.sensor_horizontal = QHBoxLayout()
        self.sensor_horizontal.setObjectName("sensor_horizontal")
        # 第一块：MPU6050 六轴传感器数据区块
        self.mpu6050_group = self._create_mpu6050_grid()
        self.sensor_horizontal.addLayout(self.mpu6050_group, stretch=2)
        # 第二块：气体传感器区块 (CO2 + TVOC)
        self.gas_group = self._create_gas_grid()
        self.sensor_horizontal.addLayout(self.gas_group, stretch=1)
        # 第三块：温湿压传感器区块
        self.env_group = self._create_env_grid()
        self.sensor_horizontal.addLayout(self.env_group, stretch=1)
        self.left_content.addLayout(self.sensor_horizontal)

        # 左侧监测部分--下方留白
        self.left_content.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        self.left_content.setStretch(0, 2)
        self.left_content.setStretch(1, 3)

        # 左侧监测部分--最下方命令输入行
        leftdown_horizontal = QHBoxLayout()
        self.sendline = QLineEdit()
        self.sendline.setPlaceholderText("输入命令并按回车发送")
        self.sendlineButton = QPushButton("发送")
        self.sendline.returnPressed.connect(self.sendText)
        self.sendlineButton.clicked.connect(self.sendText)
        leftdown_horizontal.addWidget(self.sendline)
        leftdown_horizontal.addWidget(self.sendlineButton)

        self.left_content.addLayout(leftdown_horizontal)

        self.main_horizontal.addLayout(self.left_content, stretch=4)

        # 左侧监测部分与右侧工具按钮之间的间隔
        self.main_horizontal.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Minimum)
        )

        # 设置面板
        self.right_vertical = CommandPanel()  # 直接使用 SettingsPage 作为右侧设置面板
        self.right_vertical.setFixedWidth(0)  # 初始宽度为0，表示收起状态
        self.main_horizontal.addWidget(self.right_vertical)

        # 工具按钮
        self.toolButton = QToolButton(self)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setArrowType(Qt.DownArrow)
        sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toolButton.setSizePolicy(sp)
        self.toolButton.clicked.connect(self.toggleSettingPanel)
        self.main_horizontal.addWidget(self.toolButton)

        # self.retranslateUi(self)
        # QMetaObject.connectSlotsByName(self)   

    def sendText(self):
        self.sendSignal.emit(self.sendline.text())
        self.sendline.setText("")

    def toggleSettingPanel(self):
        if self.settingExpanded:
            # 收起设置面板
            self.animateSettingPanel(expand=False)
            self.toolButton.setArrowType(Qt.DownArrow)
        else:
            # 展开设置面板
            self.animateSettingPanel(expand=True)
            self.toolButton.setArrowType(Qt.LeftArrow)

        self.settingExpanded = not self.settingExpanded

    def animateSettingPanel(self, expand: bool):
        start_width = self.right_vertical.width()
        end_width = 300 if expand else 0

        if self.anim and self.anim.state() == QPropertyAnimation.Running:
            self.anim.stop()

        self.anim = QPropertyAnimation(self.right_vertical, b"maximumWidth")
        self.anim.setDuration(300)
        self.anim.setStartValue(start_width)
        self.anim.setEndValue(end_width)
        self.anim.start()

    def _create_mpu6050_grid(self):
        """ MPU6050 六軸數據區塊 """
        grid = QGridLayout()
        grid.setObjectName("mpu6050_grid")

        # 标题
        title = QLabel("MPU6050")
        title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(title, 0, 0, 1, 4)

        # X轴
        grid.addWidget(QLabel("AX"), 1, 0)
        grid.addWidget(self.AX_label, 1, 1)
        grid.addWidget(QLabel("GX"), 1, 2)
        grid.addWidget(self.GX_label, 1, 3)

        # Y轴
        grid.addWidget(QLabel("AY"), 2, 0)
        grid.addWidget(self.AY_label, 2, 1)
        grid.addWidget(QLabel("GY"), 2, 2)
        grid.addWidget(self.GY_label, 2, 3)

        # Z轴
        grid.addWidget(QLabel("AZ"), 3, 0)
        grid.addWidget(self.AZ_label, 3, 1)
        grid.addWidget(QLabel("GZ"), 3, 2)
        grid.addWidget(self.GZ_label, 3, 3)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(3, 2)

        return grid

    def _create_gas_grid(self):
        """ 气体传感器区块 (CO2 + TVOC) """
        grid = QGridLayout()
        grid.setObjectName("gas_grid")

        title = QLabel("气体传感器")
        title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(title, 0, 0, 1, 2)

        grid.addWidget(QLabel("CO2"), 1, 0)
        grid.addWidget(self.CO2_label, 1, 1)

        grid.addWidget(QLabel("TVOC"), 2, 0)
        grid.addWidget(self.TVOC_label, 2, 1)

        grid.addItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding),
            3, 0, 1, 2
        )

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(3, 2)

        return grid

    def _create_env_grid(self):
        """ 温湿压传感器 """
        grid = QGridLayout()
        grid.setObjectName("env_grid")

        title = QLabel("温湿压传感器")
        title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(title, 0, 0, 1, 2)

        grid.addWidget(QLabel("温度"), 1, 0)
        grid.addWidget(self.TEMP_label, 1, 1)

        grid.addWidget(QLabel("湿度"), 2, 0)
        grid.addWidget(self.HUM_label, 2, 1)

        grid.addWidget(QLabel("压强"), 3, 0)
        grid.addWidget(self.PRESS_label, 3, 1)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(3, 2)

        return grid
    
class CommandPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.autoSaveStatus = True
        self.autoSaveInterval = 60

        self.serThread = None  # 用于存储串口对象
        self.serDataSignal = Signal(str)  # 定义一个信号，用于接收串口数据

        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)

        self.selectPortComboBox = QComboBox()
        self.refreshPortsButton = QPushButton("刷新")
        self.connectButton = QPushButton("连/断")
        self.setBaudrateLineEdit = QLineEdit()
        self.autosaveCheckBox = QCheckBox("启用")
        self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton("设置")

        layout.addWidget(QLabel("选择端口"), 0, 0)
        layout.addWidget(self.refreshPortsButton, 0, 1)
        layout.addWidget(self.selectPortComboBox, 1, 0)
        layout.addWidget(self.connectButton, 1, 1)
        self.comboxFillPorts()  # 初始化时填充可用串口列表
        self.refreshPortsButton.clicked.connect(self.comboxFillPorts)  # 刷新按钮连接槽函数

        layout.addWidget(QLabel("波特率"), 2, 0)
        layout.addWidget(self.setBaudrateLineEdit, 3, 0)
        self.setBaudrateLineEdit.setText("9600")  # 默认波特率

        layout.addWidget(QLabel("保存间隔(s)"), 4, 0)
        layout.addWidget(self.autosaveCheckBox, 4, 1)
        layout.addWidget(self.autosaveIntervalLineEdit, 5, 0)
        layout.addWidget(self.autosaveIntervalButton, 5, 1)
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存
        self.autosaveIntervalLineEdit.setText("60")  # 默认自动保存间隔

        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(6, 1)  # 添加伸缩项，推送内容到顶部

    def startSerialThread(self):
        currentPort = self.selectPortComboBox.currentText()
        self.serThread = SerialThread(currentPort)


    def comboxFillPorts(self):
        self.selectPortComboBox.clear()
        ports = list_ports.comports()
        if ports:
            for port in ports:
                self.selectPortComboBox.addItem(port.device)
        else:
            self.selectPortComboBox.addItem("无可用串口")
        
    def receiveData(self):
        pass



class HistoryPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout(self)
        label = QLabel("这是历史记录页面。")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        label = QLabel("设置页面")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        

class AnalysisPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        label = QLabel("这是数据分析页面。")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.textedit = QTextEdit()
        self.textedit.setReadOnly(True)
        self.textedit.textChanged.connect(self.textedit.ensureCursorVisible)
        layout.addWidget(self.textedit)
    
    def append_log(self, log: str):
        self.textedit.append(log)