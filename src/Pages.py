from PySide6.QtWidgets import (QWidget, QTabWidget, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QSpacerItem,
                            QSizePolicy, QGridLayout, QComboBox, QPushButton, QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal
from serial.tools import list_ports
from Serial import SerialThread
from PlotWidget import SensorPlotter
import os
import time

class Homepage(QWidget):
    sendTextSignal = Signal(str)
    sendErrorSignal = Signal(str)

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
        
        self.dataNames = ["AX","AY","AZ","GX","GY","GZ","CO2","TVOC","温度","湿度","压强"]
        self.MPU6050_Data = dict(zip(self.dataNames[0:6],[0 for i in range(6)]))
        self.Gas_Data = dict(zip(self.dataNames[6:8],[0 for i in range(2)]))
        self.THP_Data = dict(zip(self.dataNames[8:11],[0 for i in range(3)]))

        self.pathSave = "history"

        for label in self.labels:
            label.setStyleSheet("background-color: rgba(80,80,80,127)")

        self.anim = None  # 用于存储动画对象
        self.settingExpanded = False  # 记录设置面板的展开状态
        self.runtimeSave = None

        self.initUI()

        self.setStyleSheet('''
                        QLabel[text~="MPU6050"], QLabel[text~="气体传感器"], QLabel[text~="温湿压传感器"]
                        {background-color: #404040}
                    ''')

        self.right_vertical.serDataSignal.connect(self.updateDataDisplay)
        self.right_vertical.stopSignal.connect(self.clearData)


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
        self.env_group = self._create_thp_grid()
        self.sensor_horizontal.addLayout(self.env_group, stretch=1)
        self.left_content.addLayout(self.sensor_horizontal)

        # 左侧监测部分--下方留白
        self.RegionPlot = SensorPlotter()
        # self.left_content.addSpacerItem(
        #     QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # )
        self.left_content.addWidget(self.RegionPlot)
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
            dataList = dataText.strip("\n").split(",")
            dataListInt = list(map(eval, dataList))
            for i, data in enumerate(dataList):
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
                    self.runtimeSave.write(f"{time.time()},"+dataText+"\n")
        except Exception as e:
            self.right_vertical.serLogSignal.emit(f"错误：{e}")
    
    def clearData(self):
        for label in self.labels:
            label.setText(". . .")
        self.RegionPlot.reset()
        if self.runtimeSave:
            self.runtimeSave.close()
            self.runtimeSave = None


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
        self.anim.setDuration(200)
        self.anim.setStartValue(start_width)
        self.anim.setEndValue(end_width)
        self.anim.start()

    def _create_mpu6050_grid(self):
        """ MPU6050 """
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

    def _create_thp_grid(self):
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
    serDataSignal = Signal(str)  # 定义一个信号，用于接收串口数据
    serLogSignal = Signal(str)
    stopSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.autoSaveStatus = True
        self.autoSaveInterval = 60

        self.serThread = None  # 用于存储串口线程
        self.serState = False

        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)

        self.selectPortComboBox = QComboBox()
        self.refreshPortsButton = QPushButton("刷新")
        self.connectButton = QPushButton("连/断")
        self.BaudrateLineEdit = QLineEdit()
        self.autosaveCheckBox = QCheckBox("启用")
        self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton("设置")

        layout.addWidget(QLabel("选择端口"), 0, 0)
        layout.addWidget(self.refreshPortsButton, 0, 1)
        layout.addWidget(self.selectPortComboBox, 1, 0)
        layout.addWidget(self.connectButton, 1, 1)
        self.FillcomboxPorts()  # 初始化时填充可用串口列表
        self.refreshPortsButton.clicked.connect(self.FillcomboxPorts)  # 刷新按钮连接槽函数
        self.connectButton.clicked.connect(self.toggleSerialIO)

        layout.addWidget(QLabel("波特率"), 2, 0)
        layout.addWidget(self.BaudrateLineEdit, 3, 0)
        self.BaudrateLineEdit.setText("9600")  # 默认波特率

        layout.addWidget(QLabel("自动保存"), 4, 0)
        layout.addWidget(self.autosaveCheckBox, 4, 1)
        # layout.addWidget(self.autosaveIntervalLineEdit, 5, 0)
        # layout.addWidget(self.autosaveIntervalButton, 5, 1)
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存
        # self.autosaveIntervalLineEdit.setText("60")  # 默认自动保存间隔

        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 0)
        layout.setColumnStretch(2, 1)
        layout.setRowStretch(6, 1)  # 添加伸缩项，推送内容到顶部

    def FillcomboxPorts(self):
        self.selectPortComboBox.clear()
        ports = list_ports.comports()
        if ports:
            for port in ports:
                self.selectPortComboBox.addItem(port.device)
        else:
            self.selectPortComboBox.addItem("无可用串口")

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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
    
    def initUI(self):
        nowDir = os.getcwd()

        main_layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.pathSaveLineEdit = QLineEdit()
        self.pathSaveLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton()
        self.browserFileBtn.setText("浏览...")
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtnConfirm = QPushButton()
        self.pathBtnConfirm.setText("检索")
        self.pathBtnConfirm.clicked.connect(self.load_files)
        top_layout.addWidget(self.pathSaveLineEdit,1)
        top_layout.addWidget(self.browserFileBtn)
        top_layout.addWidget(self.pathBtnConfirm)
        main_layout.addLayout(top_layout)

        self.tabWidget = QTabWidget()
        main_layout.addWidget(self.tabWidget)
        
        localHistory_tab = QWidget()
        localHistory_layout = QVBoxLayout()
        localHistory_tab.setLayout(localHistory_layout)
        self.localListWidget = QListWidget()
        localHistory_layout.addWidget(self.localListWidget)
        self.tabWidget.addTab(localHistory_tab,"实时数据记录")
        
        self.plotBtn = QPushButton()
        self.plotBtn.setText("绘制图像")
        self.plotBtn.clicked.connect(self.plotData)
        main_layout.addWidget(self.plotBtn)

        self.RegionPlot = SensorPlotter()
        main_layout.addWidget(self.RegionPlot,1)

    def select_folder(self):
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,                    # 父窗口
            "请选择文件夹",           # 标题
            self.pathSaveLineEdit.text()    # 默认打开的路径
        )

        if folder_path:
            self.pathSaveLineEdit.setText(folder_path)
    
    def load_files(self):
        self.directory = self.pathSaveLineEdit.text().strip()
        if not os.path.isdir(self.directory):
            QMessageBox.warning(self, "Error", "无效目录路径")
            return

        self.localListWidget.clear()
        files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        # Filter for data files, e.g., .csv or .db; assuming .csv for now.
        data_files = [f for f in files if f.endswith('.csv')]  # Change to '.db' for SQLite
        if not data_files:
            QMessageBox.information(self, "Info", "无数据记录")
            return

        self.localListWidget.addItems(data_files)
    
    def plotData(self):
        selected_items = self.localListWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Info", "未选中数据记录")
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
                    dataList.append(list(map(eval, line.strip().split(','))))
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

            # # # Assuming CSV; for SQLite, use sqlite3 to query data.
            # # data = pd.read_csv(file_path)
            # # # Emit the data to the plot area signal (for future connection to plotting)
            # # self.data_loaded.emit(data)
            # # # For now, just print or handle; user can connect signal to plot function.
            # # print(f"Data loaded from {file_path}:")
            # # print(data.head())  # Placeholder action; replace with actual plotting in subclass or extension.
            
            # # If using SQLite instead:
            # import sqlite3
            # conn = sqlite3.connect(file_path)
            # #data = pd.read_sql_query("SELECT * FROM your_table", conn)  # Adjust query
            # conn.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load data: {str(e)}")
        

class SettingsPage(QWidget):
    pathSaveSignal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.initUI()

    def initUI(self):
        layout = QGridLayout(self)
        nowDir = os.getcwd()

        pathLabel = QLabel("数据保存目录")
        self.pathLineEdit = QLineEdit()
        self.pathLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton()
        self.browserFileBtn.setText("浏览...")
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtn = QPushButton()
        self.pathBtn.setText("设置")
        self.pathBtn.clicked.connect(self.on_pathBtn_click)
        layout.addWidget(pathLabel,0,0)
        layout.addWidget(self.pathLineEdit,1,0)
        layout.addWidget(self.browserFileBtn,1,1)
        layout.addWidget(self.pathBtn,1,2)
        
        layout.setColumnStretch(0,1)
        layout.setRowStretch(2,1)

    def on_pathBtn_click(self):
        directory = self.pathLineEdit.text().strip()
        self.pathSaveSignal.emit(directory)
    
    def select_folder(self):
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self,                    # 父窗口
            "请选择文件夹",           # 标题
            self.pathLineEdit.text()    # 默认打开的路径（上一次选择的路径）
        )

        if folder_path:
            self.pathLineEdit.setText(folder_path)
            self.on_pathBtn_click()

        
class AnalysisPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        label = QLabel("未实现")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.LogLevel = 0 # 0-Error 1-Warning 2-Info
        self.levelNames = ["Error","Warning","Info"]

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.LogLevelLabel = QLabel()
        self.LogLevelLabel.setText(f'日志报告等级：{self.levelNames[self.LogLevel]}')
        self.LogLevelToggleBtn = QPushButton()
        self.LogLevelToggleBtn.setText("切换")
        self.LogLevelToggleBtn.setToolTip("切换日志过滤等级")
        self.LogLevelToggleBtn.clicked.connect(self.on_LogBtn_click)

        self.textedit = QTextEdit()
        self.textedit.setReadOnly(True)
        self.textedit.textChanged.connect(self.textedit.ensureCursorVisible)

        layout.addWidget(self.LogLevelLabel)
        layout.addWidget(self.LogLevelToggleBtn)
        layout.addWidget(self.textedit,1)
    
    def on_LogBtn_click(self):
        self.LogLevel = (self.LogLevel + 1) % 3
        self.LogLevelLabel.setText(f'日志报告等级：{self.levelNames[self.LogLevel]}')

    def append_log(self, log: str, level: int):
        if level <= self.LogLevel:
            self.textedit.append(log)