from PySide6.QtWidgets import (QWidget, QTabWidget, QListWidget, QVBoxLayout, QTableWidget, QHBoxLayout, QLabel, QToolButton, QSpacerItem,
                            QSizePolicy, QGridLayout, QComboBox, QPushButton, QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox,
                            QCalendarWidget, QDialog, QStyle, QTableWidgetItem, QColorDialog, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal, QDate
from PySide6.QtGui import QColor
from serial.tools import list_ports
from Serial import SerialThread
from PlotWidget import SensorPlotter
import os
import time
from colorstyle import *
from i18n import t, set_language, get_supported_languages, get_current_language

class Homepage(QWidget):
    sendTextSignal = Signal(str)
    sendErrorSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.is_dark_theme = True  # 追踪当前主题
        
        self.AX_label = QLineEdit(". . .")
        self.AY_label = QLineEdit(". . .")
        self.AZ_label = QLineEdit(". . .")
        self.GX_label = QLineEdit(". . .")
        self.GY_label = QLineEdit(". . .")
        self.GZ_label = QLineEdit(". . .")
        self.CO2_label = QLineEdit(". . .")
        self.TVOC_label = QLineEdit(". . .")
        self.TEMP_label = QLineEdit(". . .")
        self.HUM_label = QLineEdit(". . .")
        self.PRESS_label = QLineEdit(". . .")

        self.dataBuffer = []

        self.labels = [self.AX_label, self.AY_label, self.AZ_label, self.GX_label, self.GY_label, self.GZ_label,
                        self.CO2_label, self.TVOC_label,
                        self.TEMP_label, self.HUM_label, self.PRESS_label]
        
        for label in self.labels:
            label.setReadOnly(True)
        
        self.dataNames = ["AX","AY","AZ","GX","GY","GZ","CO2","TVOC","温度","湿度","压强"]
        self.MPU6050_Data = dict(zip(self.dataNames[0:6],[0 for i in range(6)]))
        self.Gas_Data = dict(zip(self.dataNames[6:8],[0 for i in range(2)]))
        self.THP_Data = dict(zip(self.dataNames[8:11],[0 for i in range(3)]))

        self.pathSave = "history"

        for label in self.labels:
            label.setStyleSheet(get_homepage_label_stylesheet(self.is_dark_theme))

        self.anims = {"Command":None,"Sensor":None,"Plot":None}  # 用于存储动画对象
        self.settingExpanded = False  # 记录设置面板的展开状态
        self.sensorDisplay = True
        self.plotDisplay = True
        self.runtimeSave = None

        self.initUI()

        self.setStyleSheet(get_homepage_sensor_label_stylesheet(self.is_dark_theme))

        self.right_vertical.serDataSignal.connect(self.updateDataDisplay)
        self.right_vertical.stopSignal.connect(self.clearData)
        self.right_vertical.sensorDisplayCheckbox.clicked.connect(self.toggleSensorWidget)

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        # 更新所有标签样式
        for label in self.labels:
            label.setStyleSheet(get_homepage_label_stylesheet(is_dark))
        # 更新整体样式
        self.setStyleSheet(get_homepage_sensor_label_stylesheet(is_dark))
        # 更新工具按钮样式
        self.toolButton.setStyleSheet(get_tool_button_stylesheet(is_dark))
        # 更新右侧面板的样式
        self.right_vertical.update_style(is_dark)

    def update_ui_text(self):
        """更新UI文本（用于语言切换）"""
        # 更新按钮文本
        self.low_vertical_btn.setText(t("page.homepage.plot_toggle"))
        self.lowTab.setTabText(0, t("page.homepage.plot_tab"))
        self.lowTab.setTabText(1, t("page.homepage.analysis_tab"))
        self.sendline.setPlaceholderText(t("page.homepage.command_input"))
        self.sendlineButton.setText(t("page.homepage.send_button"))
        self.toolButton.setText(t("page.homepage.settings"))
        
        # 更新传感器标题
        self.mpu6050_title.setText(t("page.homepage.mpu6050"))
        self.gas_sensor_title.setText(t("page.homepage.gas_sensor"))
        self.thp_sensor_title.setText(t("page.homepage.thp_sensor"))
        
        # 更新传感器轴标签
        self.ax_label.setText(t("page.homepage.ax"))
        self.ay_label.setText(t("page.homepage.ay"))
        self.az_label.setText(t("page.homepage.az"))
        self.gx_label.setText(t("page.homepage.gx"))
        self.gy_label.setText(t("page.homepage.gy"))
        self.gz_label.setText(t("page.homepage.gz"))
        
        # 更新气体传感器标签
        self.co2_label.setText(t("page.homepage.co2"))
        self.tvoc_label.setText(t("page.homepage.tvoc"))
        
        # 更新温湿压传感器标签
        self.temp_sensor_label.setText(t("page.homepage.temperature"))
        self.humidity_sensor_label.setText(t("page.homepage.humidity"))
        self.pressure_sensor_label.setText(t("page.homepage.pressure"))
        
        # 更新右侧面板文本
        self.right_vertical.update_ui_text()


    def initUI(self):
        # 外层布局
        self.main_horizontal = QHBoxLayout(self)
        self.main_horizontal.setObjectName("main_horizontal")

        # 左侧监测部分
        self.left_content = QVBoxLayout()
        self.left_content.setObjectName("left_content")
        # 左侧监测部分--上方三块传感器数据区域
        self.sensor_widget = QWidget()
        self.sensor_horizontal = QHBoxLayout()
        self.sensor_horizontal.setObjectName("sensor_horizontal")
        # 第一块：MPU6050 六轴传感器数据区块
        self.mpu6050_group = self._create_mpu6050_grid()
        self.sensor_horizontal.addLayout(self.mpu6050_group, stretch=2)
        # 第二块：气体传感器区块 (CO2 + TVOC)
        self.gas_group = self._create_gas_grid()
        self.sensor_horizontal.addLayout(self.gas_group, stretch=1)
        # 第三块：温湿压传感器区块
        self.env_group = self._create_thp_grid()
        self.sensor_horizontal.addLayout(self.env_group, stretch=1)
        self.sensor_widget.setLayout(self.sensor_horizontal)
        self.sensor_widget.setMaximumHeight(150)
        self.left_content.addWidget(self.sensor_widget)

        # 左侧监测部分--下方留白
        self.low_vertical = QVBoxLayout()
        self.low_vertical_btn = QPushButton("显示/隐藏图表")
        self.low_vertical_btn.clicked.connect(self.togglePlotWidget)
        self.low_vertical.addWidget(self.low_vertical_btn)

        self.lowTab = QTabWidget()
        self.lowTab.setStyleSheet("* {border-radius: 0px;}")
        self.RegionPlot = SensorPlotter()
        self.lowTab.addTab(self.RegionPlot,"图像")
        self.DataAnalysis = AnalysisTab()
        self.lowTab.addTab(self.DataAnalysis,"统计")
        self.low_vertical.addWidget(self.lowTab)
        
        self.left_content.addLayout(self.low_vertical)
        self.left_content.setStretch(0, 1)
        self.left_content.setStretch(1, 8)
        self.left_content.addStretch(1)

        # 左侧监测部分--最下方命令输入行
        leftdown_horizontal = QHBoxLayout()
        self.sendline = QLineEdit()
        self.sendline.setPlaceholderText(t("page.homepage.command_input"))
        self.sendlineButton = QPushButton(t("page.homepage.send_button"))
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
        self.toolButton.setText(t("page.homepage.settings"))
        self.toolButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setStyleSheet(get_tool_button_stylesheet(self.is_dark_theme))
        self.toolButton.setArrowType(Qt.DownArrow)
        sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toolButton.setSizePolicy(sp)
        self.toolButton.clicked.connect(self.toggleSettingPanel)
        self.main_horizontal.addWidget(self.toolButton)

        # self.retranslateUi(self)
        # QMetaObject.connectSlotsByName(self)   

    def sendText(self):
        try:
            if self.right_vertical.serState:
                self.sendTextSignal.emit(self.sendline.text())
                self.right_vertical.serThread.serial.write(self.sendline.text()+"\n")
                self.sendline.setText("")
            else:
                self.sendTextSignal.emit("尚未连接")
                self.sendline.setText("")
        except Exception as e:
            self.sendErrorSignal.emit(e)

    def updateDataDisplay(self,dataText:str):
        try:
            dataList = dataText.strip().split(",")
            dataListInt = [float(x) for x in dataList]
            dataListStr = ["{:.2f}".format(x) for x in dataListInt]
            for i, data in enumerate(dataListStr):
                self.labels[i].setText(data)
            self.MPU6050_Data = dict(zip(self.dataNames[0:6],dataListInt[0:6]))
            self.Gas_Data = dict(zip(self.dataNames[6:8],dataListInt[6:8]))
            self.THP_Data = dict(zip(self.dataNames[8:11],dataListInt[8:11]))
            self.RegionPlot.update_mpu(self.MPU6050_Data)
            self.RegionPlot.update_gas(self.Gas_Data)
            self.RegionPlot.update_thp(self.THP_Data)
            if self.right_vertical.autoSaveStatus:
                if self.runtimeSave is None:
                    nowtime = time.strftime("%G_%m_%d_%H_%M_%S")
                    path = f'{self.pathSave}/localsave_{nowtime}.csv'
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    self.runtimeSave = open(path,'a+',encoding='utf-8')
                if self.runtimeSave:
                    self.runtimeSave.write(f"{time.time()},"+','.join(dataList)+"\n")
            self.dataBuffer.append(dataListInt)
            if len(self.dataBuffer) > 10000:
                self.dataBuffer.pop(0)
            if self.dataBuffer:
                transposed = list(zip(*self.dataBuffer))
                self.DataAnalysis.analysisData(transposed)
        except Exception as e:
            self.right_vertical.serLogSignal.emit(f"错误：{e}")
    
    def clearData(self):
        self.dataBuffer = []
        self.DataAnalysis.analysisData(self.dataBuffer)
        for label in self.labels:
            label.setText(". . .")
        self.RegionPlot.reset()
        if self.runtimeSave:
            self.runtimeSave.close()
            self.runtimeSave = None

    def toggleSensorWidget(self):
        startHeight = self.sensor_widget.height()
        if self.sensorDisplay:
            self.animateWidgetDisplay("Sensor", startHeight,0,self.sensor_widget,"maximumHeight")
        else:
            self.animateWidgetDisplay("Sensor", startHeight,150,self.sensor_widget,"maximumHeight")
        self.sensorDisplay = not self.sensorDisplay

    def togglePlotWidget(self):
        startHeight = self.lowTab.height()
        if self.plotDisplay:
            self.animateWidgetDisplay("Plot", startHeight,0,self.lowTab,"maximumHeight")
        else:
            self.animateWidgetDisplay("Plot", startHeight,900,self.lowTab,"maximumHeight")
        self.plotDisplay = not self.plotDisplay

    def toggleSettingPanel(self):
        startWidth = self.right_vertical.width()
        if self.settingExpanded:
            # 收起设置面板
            self.animateWidgetDisplay("Command", startWidth,0,self.right_vertical,"maximumWidth")
            self.toolButton.setArrowType(Qt.DownArrow)
        else:
            # 展开设置面板
            self.animateWidgetDisplay("Command", startWidth,300,self.right_vertical,"maximumWidth")
            self.toolButton.setArrowType(Qt.LeftArrow)
        self.settingExpanded = not self.settingExpanded

    # def animateSettingPanel(self, expand: bool):
    #     start_width = self.right_vertical.width()
    #     end_width = 300 if expand else 0

    #     if self.anim and self.anim.state() == QPropertyAnimation.Running:
    #         self.anim.stop()

    #     self.anim = QPropertyAnimation(self.right_vertical, b"maximumWidth")
    #     self.anim.setDuration(200)
    #     self.anim.setStartValue(start_width)
    #     self.anim.setEndValue(end_width)
    #     self.anim.start()
    def animateWidgetDisplay(self, anime, start, end, widget, property, duration=200):
        self.anims[anime] = QPropertyAnimation(widget, bytes(property,encoding='utf-8'))
        self.anims[anime].setDuration(duration)
        self.anims[anime].setStartValue(start)
        self.anims[anime].setEndValue(end)
        self.anims[anime].start()


    def _create_mpu6050_grid(self):
        """ MPU6050 """
        grid = QGridLayout()
        grid.setObjectName("mpu6050_grid")

        # 标题
        self.mpu6050_title = QLabel(t("page.homepage.mpu6050"))
        self.mpu6050_title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(self.mpu6050_title, 0, 0, 1, 4)

        # X轴
        self.ax_label = QLabel(t("page.homepage.ax"))
        grid.addWidget(self.ax_label, 1, 0)
        grid.addWidget(self.AX_label, 1, 1)
        self.gx_label = QLabel(t("page.homepage.gx"))
        grid.addWidget(self.gx_label, 1, 2)
        grid.addWidget(self.GX_label, 1, 3)

        # Y轴
        self.ay_label = QLabel(t("page.homepage.ay"))
        grid.addWidget(self.ay_label, 2, 0)
        grid.addWidget(self.AY_label, 2, 1)
        self.gy_label = QLabel(t("page.homepage.gy"))
        grid.addWidget(self.gy_label, 2, 2)
        grid.addWidget(self.GY_label, 2, 3)

        # Z轴
        self.az_label = QLabel(t("page.homepage.az"))
        grid.addWidget(self.az_label, 3, 0)
        grid.addWidget(self.AZ_label, 3, 1)
        self.gz_label = QLabel(t("page.homepage.gz"))
        grid.addWidget(self.gz_label, 3, 2)
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

        self.gas_sensor_title = QLabel(t("page.homepage.gas_sensor"))
        self.gas_sensor_title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(self.gas_sensor_title, 0, 0, 1, 2)

        self.co2_label = QLabel(t("page.homepage.co2"))
        grid.addWidget(self.co2_label, 1, 0)
        grid.addWidget(self.CO2_label, 1, 1)

        self.tvoc_label = QLabel(t("page.homepage.tvoc"))
        grid.addWidget(self.tvoc_label, 2, 0)
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

    def _create_thp_grid(self):
        """ 温湿压传感器 """
        grid = QGridLayout()
        grid.setObjectName("env_grid")

        self.thp_sensor_title = QLabel(t("page.homepage.thp_sensor"))
        self.thp_sensor_title.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        grid.addWidget(self.thp_sensor_title, 0, 0, 1, 2)

        self.temp_sensor_label = QLabel(t("page.homepage.temperature"))
        grid.addWidget(self.temp_sensor_label, 1, 0)
        grid.addWidget(self.TEMP_label, 1, 1)

        self.humidity_sensor_label = QLabel(t("page.homepage.humidity"))
        grid.addWidget(self.humidity_sensor_label, 2, 0)
        grid.addWidget(self.HUM_label, 2, 1)

        self.pressure_sensor_label = QLabel(t("page.homepage.pressure"))
        grid.addWidget(self.pressure_sensor_label, 3, 0)
        grid.addWidget(self.PRESS_label, 3, 1)

        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 2)
        grid.setRowStretch(2, 2)
        grid.setRowStretch(3, 2)

        return grid
    
class CommandPanel(QWidget):
    serDataSignal = Signal(str)  # 定义一个信号，用于接收串口数据
    serLogSignal = Signal(str)
    stopSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_dark_theme = True  # 追踪当前主题
        
        self.autoSaveStatus = True
        self.autoSaveInterval = 60

        self.serThread = None  # 用于存储串口线程
        self.serState = False

        self.initUI()

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        colors = get_theme_colors(is_dark)
        # 这里可以添加更多的样式更新逻辑

    def update_ui_text(self):
        """更新UI文本（用于语言切换）"""
        self.refreshPortsButton.setText(t("command_panel.refresh"))
        self.connectButton.setText(t("command_panel.connect"))
        self.autosaveCheckBox.setText(t("command_panel.enable"))
        self.sensorDisplayCheckbox.setText(t("command_panel.dashboard"))

    def initUI(self):
        self.gridlayout = QGridLayout(self)

        self.selectPortComboBox = QComboBox()
        self.refreshPortsButton = QPushButton(t("command_panel.refresh"))
        self.connectButton = QPushButton(t("command_panel.connect"))
        self.BaudrateLineEdit = QLineEdit()
        self.autosaveCheckBox = QCheckBox(t("command_panel.enable"))
        # self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton(t("command_panel.set"))
        self.sensorDisplayCheckbox = QCheckBox(t("command_panel.dashboard"))
        self.TextCopy = QTextEdit()
        self.TextCopy.setReadOnly(True)
        

        self.gridlayout.addWidget(QLabel(t("command_panel.select_port")), 0, 0)
        self.gridlayout.addWidget(self.refreshPortsButton, 0, 1)
        self.gridlayout.addWidget(self.selectPortComboBox, 1, 0)
        self.gridlayout.addWidget(self.connectButton, 1, 1)
        self.FillcomboxPorts()  # 初始化时填充可用串口列表
        self.refreshPortsButton.clicked.connect(self.FillcomboxPorts)  # 刷新按钮连接槽函数
        self.connectButton.clicked.connect(self.toggleSerialIO)


        self.gridlayout.addWidget(QLabel(t("command_panel.baudrate")), 2, 0)
        self.gridlayout.addWidget(self.BaudrateLineEdit, 3, 0)
        self.BaudrateLineEdit.setText("9600")  # 默认波特率

        self.gridlayout.addWidget(QLabel(t("command_panel.auto_save")), 4, 0)
        self.gridlayout.addWidget(self.autosaveCheckBox, 4, 1)
        # layout.addWidget(self.autosaveIntervalLineEdit, 5, 0)
        # layout.addWidget(self.autosaveIntervalButton, 5, 1)
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存
        # self.autosaveIntervalLineEdit.setText("60")  # 默认自动保存间隔

        self.gridlayout.addWidget(self.sensorDisplayCheckbox,5,0,1,2)
        self.sensorDisplayCheckbox.setChecked(True)

        self.gridlayout.addWidget(self.TextCopy,6,0,1,2)

        self.gridlayout.setColumnStretch(0, 4)
        self.gridlayout.setColumnStretch(1, 0)
        self.gridlayout.setColumnStretch(2, 0)
        self.gridlayout.setRowStretch(6, 1)  # 添加伸缩项，推送内容到顶部

    def FillcomboxPorts(self):
        self.selectPortComboBox.clear()
        ports = list_ports.comports()
        if ports:
            for port in ports:
                self.selectPortComboBox.addItem(port.device)
        else:
            self.selectPortComboBox.addItem(t("command_panel.no_ports"))

    def toggleSerialIO(self):
        if self.serState:
            self.stopSerialThread()
            self.stopSignal.emit()
        else:
            self.startSerialThread()


    def startSerialThread(self):
        try:
            self.stopSerialThread()
            currentPort = self.selectPortComboBox.currentText()
            baudrate = int(self.BaudrateLineEdit.text())
            self.serThread = SerialThread(currentPort,baudrate,timeout=1)
            self.serThread.data_signal.connect(self.serDataSignal.emit)
            self.serThread.status_signal.connect(self.serLogSignal.emit)
            self.serThread.stop_signal.connect(self.stopSerialThread)
            self.serThread.start()
            self.serState = True
        except Exception as e:
            self.serDataSignal.emit(f"Error: {e}")
        
    def stopSerialThread(self):
        if self.serState:
            self.serThread.stop()
            self.serState = False
            
    
    def LogText(self,text):
        self.serDataSignal.emit(text)



class HistoryPage(QWidget):
    errorSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_dark_theme = True  # 追踪当前主题

        self.msg = QMessageBox()
        self.msg.setOption(QMessageBox.DontUseNativeDialog, True)
        self.msg.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))

        self.dialog = QFileDialog()
        self.dialog.setWindowTitle(t("page.history.select_folder"))
        self.dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.dialog.setStyleSheet('''
                    * {
                        padding: 0px;
                        border: 0px;
                        margin: 0px;
                        }    
                    ''')
        self.dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        self.dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        
        self.initUI()

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        # HistoryPage的样式主要由qt_material处理，这里保留接口以保持一致性
    
    def update_ui_text(self):
        """更新UI文本（用于语言切换）"""
        self.browserFileBtn.setText(t("page.history.browse"))
        self.pathBtnConfirm.setText(t("page.history.retrieve"))
        self.calendarButton.setText(t("page.history.select_date"))
        self.DateCheck.setText(t("page.history.enable"))
        self.tabWidget.setTabText(0, t("page.history.select_data"))
        self.tabWidget.setTabText(1, t("page.history.preview_data"))
        self.tabWidget.setTabText(2, t("page.history.analysis_tab"))
        self.plotBtn.setText(t("page.history.plot_image"))
    
    def initUI(self):
        nowDir = os.getcwd()

        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.pathSaveLineEdit = QLineEdit()
        self.pathSaveLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton()
        self.browserFileBtn.setText(t("page.history.browse"))
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtnConfirm = QPushButton()
        self.pathBtnConfirm.setText(t("page.history.retrieve"))
        self.pathBtnConfirm.clicked.connect(self.load_files)
        top_layout.addWidget(self.pathSaveLineEdit,1)
        top_layout.addWidget(self.browserFileBtn)
        top_layout.addWidget(self.pathBtnConfirm)
        main_layout.addLayout(top_layout)

        date_layout = QHBoxLayout()
        self.calendarButton = QPushButton()
        self.calendarButton.setText(t("page.history.select_date"))
        self.calendarButton.clicked.connect(self.show_date_picker)
        self.DateLabel = QLineEdit()
        self.DateLabel.setReadOnly(True)
        self.DateLabel.setText(QDate.currentDate().toString(Qt.DateFormat.ISODate))
        # self.YearDate = QComboBox()
        # self.MonthDate = QComboBox()
        # self.DayDate = QComboBox()

        self.DateCheck = QCheckBox()
        self.DateCheck.setText(t("page.history.enable"))
        date_layout.addWidget(self.calendarButton)
        date_layout.addWidget(self.DateLabel,1)
        # date_layout.addWidget(self.YearDate,1)
        # date_layout.addWidget(self.MonthDate,1)
        # date_layout.addWidget(self.DayDate,1)
        date_layout.addWidget(self.DateCheck)
        main_layout.addLayout(date_layout)

        self.tabWidget = QTabWidget()
        main_layout.addWidget(self.tabWidget)
        
        localHistory_tab = QWidget()
        localHistory_layout = QVBoxLayout()
        localHistory_tab.setLayout(localHistory_layout)
        self.localListWidget = QListWidget()
        localHistory_layout.addWidget(self.localListWidget)
        self.tabWidget.addTab(localHistory_tab,t("page.history.select_data"))

        self.DataPreview_tab = QTableWidget()
        self.DataPreview_tab.setStyleSheet("* {border-radius: 0px;}")
        self.tabWidget.addTab(self.DataPreview_tab,t("page.history.preview_data"))

        self.DataAnalysis = AnalysisTab()
        self.DataAnalysis.setStyleSheet("* {border-radius: 0px;}")
        self.tabWidget.addTab(self.DataAnalysis,t("page.history.analysis_tab"))
        
        self.plotBtn = QPushButton()
        self.plotBtn.setText(t("page.history.plot_image"))
        self.plotBtn.clicked.connect(self.plotData)
        main_layout.addWidget(self.plotBtn)

        self.RegionPlot = SensorPlotter()
        self.RegionPlot.setStyleSheet("* {border-radius: 0px;}")
        main_layout.addWidget(self.RegionPlot,1)

    # def select_folder(self):
    #     dialog = QFileDialog()
    #     dialog.setWindowTitle("请选择文件夹")
    #     dialog.setFileMode(QFileDialog.FileMode.Directory)
    #     dialog.setStyleSheet('''
    #                 * {
    #                     padding: 0px;
    #                     border: 0px;
    #                     margin: 0px;
    #                     }    
    #                 ''')
    #     dialog.setOption(QFileDialog.DontUseNativeDialog, True)
    #     dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))

    #     if self.pathSaveLineEdit.text():
    #         dialog.setDirectory(self.pathSaveLineEdit.text())
    #     else:
    #         dialog.setDirectory(os.getcwd())

    #     if dialog.exec():
    #         self.pathSaveLineEdit.setText(dialog.selectedFiles()[0])

    def select_folder(self):
        last_path = self.pathSaveLineEdit.text() if self.pathSaveLineEdit.text() else os.getcwd()
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self.dialog,                    # 父窗口
            t("page.history.select_folder"),           # 标题
            last_path,    # 默认打开的路径（上一次选择的路径）
            QFileDialog.DontUseNativeDialog
        )

        if folder_path:
            self.pathSaveLineEdit.setText(folder_path)

    def show_date_picker(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(t("page.history.select_date"))
        dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        dialog.setModal(True)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        # 可选：默认选中今天
        calendar.setSelectedDate(QDate.currentDate())
        
        ok_btn = QPushButton(t("page.history.confirm"))
        ok_btn.clicked.connect(lambda: self.on_date_selected(calendar, dialog))
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(calendar)
        layout.addWidget(ok_btn)
        
        dialog.resize(640, 280)
        dialog.exec()
    
    def on_date_selected(self, calendar, dialog):
        date = calendar.selectedDate()
        date_str = date.toString("yyyy-MM-dd")
        self.DateLabel.setText(date_str)
        dialog.accept()
    
    def load_files(self):
        data_files = []
        self.directory = self.pathSaveLineEdit.text().strip()
        if not os.path.isdir(self.directory):
            self.msg.warning(self.msg, "Error", t("page.history.invalid_directory"))
            return

        self.localListWidget.clear()
        files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        # Filter for data files, e.g., .csv or .db; assuming .csv for now.
        data_files = [f for f in files if f.endswith('.csv')]  # Change to '.db' for SQLite
        if self.DateCheck.isChecked():
            date = '_'.join(self.DateLabel.text().split("-"))
            data_files[:] = [f for f in data_files if f.startswith("localsave_") and f[10:20] == date]
        if not data_files:
            self.msg.information(self.msg, "Info", t("page.history.no_data"))
            return

        self.localListWidget.addItems(data_files)
    
    def plotData(self):
        selected_items = self.localListWidget.selectedItems()
        if not selected_items:
            self.msg.information(self.msg, "Info", t("page.history.no_data_selected"))
            return

        selected_file = selected_items[0].text()
        file_path = os.path.join(self.directory, selected_file)

        try:

            with open(file_path,'r',encoding='utf-8') as f:
                dataList = []
                total_names = ['AX','AY','AZ','GX','GY','GZ','CO2','TVOC','温度','湿度','压强']
                mpu_dist = {'AX':{'times':[],'values':[]},'AY':{'times':[],'values':[]},'AZ':{'times':[],'values':[]},
                            'GX':{'times':[],'values':[]},'GY':{'times':[],'values':[]},'GZ':{'times':[],'values':[]}}
                gas_dist = {'CO2':{'times':[],'values':[]},'TVOC':{'times':[],'values':[]}}
                thp_dist = {'温度':{'times':[],'values':[]},'湿度':{'times':[],'values':[]},'压强':{'times':[],'values':[]}}
                for line in f:
                    #dataList.append(list(map(eval, line.strip().split(','))))
                    dataList.append([float(x) for x in line.strip().split(',')])
                dataList = list(zip(*dataList))
                for i, name in enumerate(total_names):
                    if i < 6:
                        mpu_dist[name]['times'] = dataList[0]
                        mpu_dist[name]['values'] = dataList[i+1]
                    if i > 5 and i < 8:
                        gas_dist[name]['times'] = dataList[0]
                        gas_dist[name]['values'] = dataList[i+1]
                    if i > 7:
                        thp_dist[name]['times'] = dataList[0]
                        thp_dist[name]['values'] = dataList[i+1]

                self.RegionPlot.load_mpu_history(mpu_dist)
                self.RegionPlot.load_gas_history(gas_dist)
                self.RegionPlot.load_thp_history(thp_dist)

                space = 10
                self.DataPreview_tab.setRowCount(len(dataList[0])+space)
                self.DataPreview_tab.setColumnCount(len(dataList)+space)
                self.DataPreview_tab.setHorizontalHeaderLabels(['时间',*total_names,*['' for x in range(space)]])

                previewDataList = [[str(i) for i in x] for x in dataList]
                #previewDataList[0] = list(map(lambda x:time.strftime("%Y-%m-%d %H:%M:%S",x), map(time.localtime,map(eval,previewDataList[0]))))
                previewDataList[0] = [time.strftime("%Y-%m-%d %H:%M:%S",i) for i in [time.localtime(x) for x in dataList[0]]]

                for column in range(len(previewDataList)):
                    for row in range(len(previewDataList[column])):
                        self.DataPreview_tab.setItem(row,column,QTableWidgetItem(previewDataList[column][row]))

                self.DataPreview_tab.resizeColumnsToContents()

                analysisDataList = dataList.copy()
                analysisDataList.pop(0)
                self.DataAnalysis.analysisData(analysisDataList)
            
        except Exception as e:
            self.msg.warning(self.msg, "Error", f"Failed to load data: {str(e)}")
 

class SettingsPage(QWidget):
    pathSaveSignal = Signal(str)
    styleSignal = Signal(str)
    themeColorsChangedSignal = Signal(bool)  # True表示深色主题，False表示浅色主题
    languageChangedSignal = Signal(str)  # 语言改变信号

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_dark_theme = True  # 追踪当前主题
        # 加载保存的主题颜色
        load_theme_colors()

        self.dialog = QFileDialog()
        self.dialog.setWindowTitle(t("page.settings.title"))
        self.dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.dialog.setStyleSheet('''
                    * {
                        padding: 0px;
                        border: 0px;
                        margin: 0px;
                        }    
                    ''')
        self.dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        self.dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        
        self.initUI()

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        # SettingsPage的样式主要由qt_material处理，这里保留接口以保持一致性
    
    def update_ui_text(self):
        """更新所有UI文本"""
        # 更新对话框标题
        self.dialog.setWindowTitle(t("page.settings.title"))
        
        # 更新路径相关按钮
        self.browserFileBtn.setText(t("page.settings.browse"))
        self.pathBtn.setText(t("page.settings.set"))
        
        # 更新样式应用按钮
        self.styleApply.setText(t("page.settings.apply"))
        
        # 更新重置按钮
        self.resetColorBtn.setText(t("page.settings.reset_colors"))
        
        # 更新主题编辑标签
        self.themeEditLabel.setText(t("page.settings.edit_theme"))
        
        # 更新颜色标签
        self.colorLabel.setText(t("page.settings.custom_colors"))
        
        # 更新语言选择标签和按钮
        self.languageLabel.setText(t("page.settings.language"))
        
        # 重新创建颜色面板以更新标签
        self.create_color_panel()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        
        # ===== 数据保存目录部分 =====
        path_layout = QGridLayout()
        nowDir = os.getcwd()

        pathLabel = QLabel(t("page.settings.save_directory"))
        self.pathLineEdit = QLineEdit()
        self.pathLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton(t("page.settings.browse"))
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtn = QPushButton(t("page.settings.set"))
        self.pathBtn.clicked.connect(self.on_pathBtn_click)
        path_layout.addWidget(pathLabel, 0, 0)
        path_layout.addWidget(self.pathLineEdit, 1, 0)
        path_layout.addWidget(self.browserFileBtn, 1, 1)
        path_layout.addWidget(self.pathBtn, 1, 2)
        main_layout.addLayout(path_layout)

        # ===== 语言选择部分 =====
        language_layout = QGridLayout()
        self.languageLabel = QLabel(t("page.settings.language"))
        self.languageCombo = QComboBox()
        
        # 获取支持的语言
        supported_langs = get_supported_languages()
        for lang_code, lang_name in supported_langs.items():
            self.languageCombo.addItem(lang_name, lang_code)
        
        # 设置当前语言
        current_lang = get_current_language()
        for i in range(self.languageCombo.count()):
            if self.languageCombo.itemData(i) == current_lang:
                self.languageCombo.setCurrentIndex(i)
                break
        
        self.languageCombo.currentIndexChanged.connect(self.on_language_changed)
        language_layout.addWidget(self.languageLabel, 0, 0)
        language_layout.addWidget(self.languageCombo, 0, 1)
        language_layout.setColumnStretch(1,1)
        main_layout.addLayout(language_layout)

        # ===== qt_material主题部分 =====
        style_layout = QGridLayout()
        self.styleCombobox = QComboBox()
        style_dict = {
            '深琥珀'     : 'dark_amber.xml',
            '深蓝'       : 'dark_blue.xml',
            '深青'       : 'dark_cyan.xml',
            '深浅绿'     : 'dark_lightgreen.xml',
            '深粉'       : 'dark_pink.xml',
            '深紫'       : 'dark_purple.xml',
            '深红'       : 'dark_red.xml',
            '深青绿'     : 'dark_teal.xml',
            '深黄'       : 'dark_yellow.xml',
            
            '浅琥珀'     : 'light_amber.xml',
            '浅蓝'       : 'light_blue.xml',
            '鲜浅蓝'   : 'light_blue_500.xml',
            '浅青'       : 'light_cyan.xml',
            '鲜浅青'   : 'light_cyan_500.xml',
            '浅绿'       : 'light_lightgreen.xml',
            '鲜浅绿'   : 'light_lightgreen_500.xml',
            '浅橙'       : 'light_orange.xml',
            '浅粉'       : 'light_pink.xml',
            '鲜鲜浅粉'   : 'light_pink_500.xml',
            '浅紫'       : 'light_purple.xml',
            '鲜浅紫'   : 'light_purple_500.xml',
            '浅红'       : 'light_red.xml',
            '鲜浅红'   : 'light_red_500.xml',
            '浅青绿'     : 'light_teal.xml',
            '鲜浅青绿' : 'light_teal_500.xml',
            '浅黄'       : 'light_yellow.xml',
        }
        self.style_dict = style_dict
        self.styleCombobox.addItems(style_dict.keys())
        self.styleCombobox.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.styleCombobox.setMaxVisibleItems(8)
        self.styleApply = QPushButton(t("page.settings.apply"))
        self.styleApply.clicked.connect(lambda: self.styleSignal.emit(style_dict[self.styleCombobox.currentText()]))
        style_layout.addWidget(QLabel(t("page.settings.material_theme")), 0, 0)
        style_layout.addWidget(self.styleCombobox, 1, 0)
        style_layout.addWidget(self.styleApply, 1, 1)
        main_layout.addLayout(style_layout)

        # ===== 自定义颜色部分 =====
        self.colorLabel = QLabel(t("page.settings.custom_colors"))
        self.colorLabel.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
        main_layout.addWidget(self.colorLabel)

        # 选择要编辑的主题
        theme_layout = QHBoxLayout()
        self.themeEditLabel = QLabel(t("page.settings.edit_theme"))
        theme_layout.addWidget(self.themeEditLabel)
        self.themeTypeCombo = QComboBox()
        self.themeTypeCombo.addItems([t("page.settings.dark_theme"), t("page.settings.light_theme")])
        self.themeTypeCombo.setMinimumWidth(150)
        self.themeTypeCombo.currentIndexChanged.connect(self.on_theme_type_changed)
        theme_layout.addWidget(self.themeTypeCombo)
        theme_layout.addStretch()
        main_layout.addLayout(theme_layout)

        # 颜色选择面板
        self.color_panel_layout = QGridLayout()
        self.color_buttons = {}
        self.create_color_panel()
        main_layout.addLayout(self.color_panel_layout)

        # 重置按钮
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        self.resetColorBtn = QPushButton(t("page.settings.reset_colors"))
        self.resetColorBtn.clicked.connect(self.reset_theme_colors)
        reset_layout.addWidget(self.resetColorBtn)
        main_layout.addLayout(reset_layout)

        # 添加伸缩项
        main_layout.addStretch()

    def create_color_panel(self):
        """创建颜色选择面板"""
        # 清空旧的布局
        while self.color_panel_layout.count():
            item = self.color_panel_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.color_buttons = {}
        is_dark = self.themeTypeCombo.currentIndex() == 0
        current_colors = dark_theme_colors if is_dark else light_theme_colors
        
        color_names = ["Background", "Surface", "Text_Primary", "Text_Secondary", "Accent", "Border_Hover"]
        color_label_keys = ["color.background", "color.surface", "color.text_primary", "color.text_secondary", "color.accent", "color.border_hover"]
        
        for i, (color_key, color_label_key) in enumerate(zip(color_names, color_label_keys)):
            label = QLabel(t(color_label_key))
            label.setMinimumWidth(80)
            
            # 创建颜色按钮
            btn = QPushButton()
            btn.setFixedSize(60, 30)
            color = current_colors.get(color_key, "#000000")
            btn.setStyleSheet(f"background-color: {color}; border: 1px solid #666; border-radius: 3px;")
            btn.clicked.connect(lambda checked, key=color_key, is_dark=is_dark: 
                               self.on_color_button_clicked(key, is_dark))
            
            # 创建颜色值显示标签
            value_label = QLineEdit(color)
            value_label.setReadOnly(True)
            value_label.setMinimumWidth(100)
            
            self.color_buttons[color_key] = {
                'button': btn,
                'value_label': value_label,
                'label': label
            }
            
            row = i
            self.color_panel_layout.addWidget(label, row, 0)
            self.color_panel_layout.addWidget(btn, row, 1)
            self.color_panel_layout.addWidget(value_label, row, 2)

    def on_color_button_clicked(self, color_key: str, is_dark: bool):
        """处理颜色按钮点击事件"""
        current_colors = dark_theme_colors if is_dark else light_theme_colors
        current_color = current_colors.get(color_key, "#000000")
        
        # 打开颜色选择对话框
        color = QColorDialog.getColor(
            QColor(current_color),
            self,
            f"选择{color_key}颜色"
        )
        
        if color.isValid():
            hex_color = color.name()
            # 更新颜色
            current_colors[color_key] = hex_color
            
            # 保存到文件
            save_theme_colors(is_dark, current_colors)
            
            # 更新按钮显示
            self.color_buttons[color_key]['button'].setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid #666; border-radius: 3px;"
            )
            self.color_buttons[color_key]['value_label'].setText(hex_color)
            
            # 发出信号通知主窗口更新样式
            self.themeColorsChangedSignal.emit(is_dark)

    def on_theme_type_changed(self):
        """处理主题类型改变"""
        self.create_color_panel()
    
    def on_language_changed(self, index):
        """处理语言改变"""
        language_code = self.languageCombo.itemData(index)
        if set_language(language_code):
            self.languageChangedSignal.emit(language_code)

    def reset_theme_colors(self):
        """重置主题颜色为默认值"""
        is_dark = self.themeTypeCombo.currentIndex() == 0
        reset_theme_colors(is_dark)
        self.create_color_panel()
        self.themeColorsChangedSignal.emit(is_dark)
        QMessageBox.information(self, "提示", "已重置为默认颜色")

    def on_pathBtn_click(self):
        directory = self.pathLineEdit.text().strip()
        self.pathSaveSignal.emit(directory)
    
    def select_folder(self):
        last_path = self.pathLineEdit.text() if self.pathLineEdit.text() else os.getcwd()
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self.dialog,                    # 父窗口
            "请选择文件夹",           # 标题
            last_path,    # 默认打开的路径（上一次选择的路径）
            QFileDialog.DontUseNativeDialog
        )

        if folder_path:
            self.pathLineEdit.setText(folder_path)
            self.on_pathBtn_click()
        
class AnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark_theme = True  # 追踪当前主题
        self.initUI()

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        # AnalysisTab的样式主要由qt_material处理，这里保留接口以保持一致性

    def update_ui_text(self):
        """更新UI文本（用于语言切换）"""
        # 更新传感器名称
        dataNames = [
            t("page.homepage.ax"), t("page.homepage.ay"), t("page.homepage.az"),
            t("page.homepage.gx"), t("page.homepage.gy"), t("page.homepage.gz"),
            t("page.homepage.co2"), t("page.homepage.tvoc"),
            t("page.homepage.temperature"), t("page.homepage.humidity"), t("page.homepage.pressure")
        ]
        
        # 更新统计值名称
        valueNames = [t("page.analysis.mean"), t("page.analysis.median"), t("page.analysis.std_dev")]
        
        self.dataNames = dataNames
        self.valueNames = valueNames
        
        # 更新表格标题
        self.dataTable.setHorizontalHeaderLabels([*valueNames,*['' for i in range(27)]])
        self.dataTable.setVerticalHeaderLabels([*dataNames,*['' for i in range(19)]])

    def initUI(self):
        self.main_layout = QVBoxLayout(self)

        # 使用翻译函数获取传感器名称
        dataNames = [
            t("page.homepage.ax"), t("page.homepage.ay"), t("page.homepage.az"),
            t("page.homepage.gx"), t("page.homepage.gy"), t("page.homepage.gz"),
            t("page.homepage.co2"), t("page.homepage.tvoc"),
            t("page.homepage.temperature"), t("page.homepage.humidity"), t("page.homepage.pressure")
        ]
        
        # 使用翻译函数获取统计值名称
        valueNames = [t("page.analysis.mean"), t("page.analysis.median"), t("page.analysis.std_dev")]
        
        self.dataNames = dataNames
        self.valueNames = valueNames
        
        self.dataTable = QTableWidget()
        self.dataTable.setRowCount(30)
        self.dataTable.setColumnCount(30)
        self.dataTable.setHorizontalHeaderLabels([*valueNames,*['' for i in range(27)]])
        self.dataTable.setVerticalHeaderLabels([*dataNames,*['' for i in range(19)]])
        self.dataTable.resizeColumnsToContents()
        self.dataTable.setEditTriggers(self.dataTable.editTriggers().NoEditTriggers)
        self.main_layout.addWidget(self.dataTable)

    # def updateCurrent(self,dataList):
    #     for i,data in enumerate(dataList):
    #             self.currentTable.setItem(i,1,QTableWidgetItem(str(data)))

    def analysisData(self,dataList):
        if dataList:
            #data_mean = list(map(lambda x: "{:.2f}".format(sum(x)/len(x)), dataList))
            data_mean = ["{:.2f}".format(sum(x)/len(x)) for x in dataList]
            #data_median = list(map(lambda x: "{:.2f}".format((x[len(x)//2-1]+x[len(x)//2])/2) if len(x)%2==0 else "{:.2f}".format(x[(len(x)-1)//2]),list(map(sorted, dataList))))
            dataListSort = [sorted(data) for data in dataList]
            data_median = ['{:.2f}'.format((x[len(x)//2-1]+x[len(x)//2])/2) if len(x)%2==0 else '{:.2f}'.format(x[(len(x)-1)//2]) for x in dataListSort]
            #data_std = list(map(lambda mean,data: "{:.2f}".format((sum((x-eval(mean))**2 for x in data)/len(data))**(1/2)), data_mean, dataList))
            data_std = ["{:.2f}".format((sum([(x-float(mean))**2 for x in data])/len(data))**(1/2)) for mean,data in zip(data_mean,dataList)]
            data_result = [data_mean,data_median,data_std]
            for column,value in enumerate(data_result):
                for row,data in enumerate(value):
                    self.dataTable.setItem(row,column,QTableWidgetItem(data))
        else:
            self.dataTable.clearContents()

    # def analysisHistoryData(self,dataList):
    #     dataList.pop(0)
    #     data_average = list(map(lambda x: sum(x)/len(x), dataList))

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_dark_theme = True  # 追踪当前主题
        self.LogLevel = 0 # 0-Error 1-Warning 2-Info
        self.levelNames = [t("page.log.error"), t("page.log.warning"), t("page.log.info")]

        self.initUI()

    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        # LogPage的样式主要由qt_material处理，这里保留接口以保持一致性

    def update_ui_text(self):
        """更新UI文本（用于语言切换）"""
        self.levelNames = [t("page.log.error"), t("page.log.warning"), t("page.log.info")]
        self.LogLevelLabel.setText(f'{t("page.log.level")}{self.levelNames[self.LogLevel]}')
        self.LogLevelToggleBtn.setText(t("page.log.toggle"))
        self.LogLevelToggleBtn.setToolTip(t("page.log.toggle_tooltip"))
        self.clearBtn.setText(t("page.log.clear"))

    def initUI(self):
        layout = QVBoxLayout(self)
        self.LogLevelLabel = QLabel()
        self.LogLevelLabel.setText(f'{t("page.log.level")}{self.levelNames[self.LogLevel]}')
        self.LogLevelToggleBtn = QPushButton()
        self.LogLevelToggleBtn.setText(t("page.log.toggle"))
        self.LogLevelToggleBtn.setToolTip(t("page.log.toggle_tooltip"))
        self.LogLevelToggleBtn.clicked.connect(self.on_LogBtn_click)

        self.clearBtn = QPushButton()
        self.clearBtn.setText(t("page.log.clear"))
        self.clearBtn.clicked.connect(self.clearText)

        self.textedit = QTextEdit()
        self.textedit.setReadOnly(True)
        self.textedit.textChanged.connect(self.textedit.ensureCursorVisible)

        layout.addWidget(self.LogLevelLabel)
        layout.addWidget(self.LogLevelToggleBtn)
        layout.addWidget(self.clearBtn)
        layout.addWidget(self.textedit,1)
    
    def on_LogBtn_click(self):
        self.LogLevel = (self.LogLevel + 1) % 3
        self.LogLevelLabel.setText(f'{t("page.log.level")}{self.levelNames[self.LogLevel]}')

    def clearText(self):
        self.textedit.clear()

    def append_log(self, log: str, level: int):
        if level <= self.LogLevel:
            self.textedit.append(log)