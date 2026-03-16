from PySide6.QtWidgets import (QWidget, QTabWidget, QListWidget, QVBoxLayout, QTableWidget, QHBoxLayout, QLabel, QToolButton, QSpacerItem,
                            QSizePolicy, QGridLayout, QComboBox, QPushButton, QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox,
                            QCalendarWidget, QDialog, QStyle, QTableWidgetItem)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal, QDate
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

        self.dataBuffer = []

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
        self.lowTab = QTabWidget()
        self.lowTab.setStyleSheet("* {border-radius: 0px;}")
        self.RegionPlot = SensorPlotter()
        self.lowTab.addTab(self.RegionPlot,"图像")
        self.DataAnalysis = AnalysisTab()
        self.lowTab.addTab(self.DataAnalysis,"统计")
        # self.left_content.addSpacerItem(
        #     QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # )

        self.left_content.addWidget(self.lowTab)
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
        self.toolButton.setStyleSheet("* {background-color: #404040}")
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
            dataListInt = list(map(eval, dataList))
            dataList = list(map(lambda x: "{:.2f}".format(x),dataListInt))
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
                    self.runtimeSave.write(f"{time.time()},"+','.join(dataList)+"\n")
            self.dataBuffer.append(dataListInt)
            self.dataBuffer = list(zip(*self.dataBuffer))
            self.DataAnalysis.analysisData(self.dataBuffer)
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
        self.gridlayout = QGridLayout(self)

        self.selectPortComboBox = QComboBox()
        self.refreshPortsButton = QPushButton("刷新")
        self.connectButton = QPushButton("连/断")
        self.BaudrateLineEdit = QLineEdit()
        self.autosaveCheckBox = QCheckBox("启用")
        self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton("设置")

        self.gridlayout.addWidget(QLabel("选择端口"), 0, 0)
        self.gridlayout.addWidget(self.refreshPortsButton, 0, 1)
        self.gridlayout.addWidget(self.selectPortComboBox, 1, 0)
        self.gridlayout.addWidget(self.connectButton, 1, 1)
        self.FillcomboxPorts()  # 初始化时填充可用串口列表
        self.refreshPortsButton.clicked.connect(self.FillcomboxPorts)  # 刷新按钮连接槽函数
        self.connectButton.clicked.connect(self.toggleSerialIO)

        self.gridlayout.addWidget(QLabel("波特率"), 2, 0)
        self.gridlayout.addWidget(self.BaudrateLineEdit, 3, 0)
        self.BaudrateLineEdit.setText("9600")  # 默认波特率

        self.gridlayout.addWidget(QLabel("自动保存"), 4, 0)
        self.gridlayout.addWidget(self.autosaveCheckBox, 4, 1)
        # layout.addWidget(self.autosaveIntervalLineEdit, 5, 0)
        # layout.addWidget(self.autosaveIntervalButton, 5, 1)
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存
        # self.autosaveIntervalLineEdit.setText("60")  # 默认自动保存间隔

        self.gridlayout.setColumnStretch(0, 4)
        self.gridlayout.setColumnStretch(1, 0)
        self.gridlayout.setColumnStretch(2, 0)
        self.gridlayout.setRowStretch(5, 1)  # 添加伸缩项，推送内容到顶部

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

        self.msg = QMessageBox()
        self.msg.setOption(QMessageBox.DontUseNativeDialog, True)
        self.msg.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))

        self.dialog = QFileDialog()
        self.dialog.setWindowTitle("请选择文件夹")
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

        date_layout = QHBoxLayout()
        self.calendarButton = QPushButton()
        self.calendarButton.setText("选择日期")
        self.calendarButton.clicked.connect(self.show_date_picker)
        self.DateLabel = QLineEdit()
        self.DateLabel.setReadOnly(True)
        self.DateLabel.setText(QDate.currentDate().toString(Qt.DateFormat.ISODate))
        # self.YearDate = QComboBox()
        # self.MonthDate = QComboBox()
        # self.DayDate = QComboBox()

        self.DateCheck = QCheckBox()
        self.DateCheck.setText("启用")
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
        self.tabWidget.addTab(localHistory_tab,"选择数据")

        self.DataPreview_tab = QTableWidget()
        self.DataPreview_tab.setStyleSheet("* {border-radius: 0px;}")
        self.tabWidget.addTab(self.DataPreview_tab,"预览数据")

        self.DataAnalysis = AnalysisTab()
        self.DataAnalysis.setStyleSheet("* {border-radius: 0px;}")
        self.tabWidget.addTab(self.DataAnalysis,"统计")
        
        self.plotBtn = QPushButton()
        self.plotBtn.setText("绘制图像")
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
            "请选择文件夹",           # 标题
            last_path,    # 默认打开的路径（上一次选择的路径）
            QFileDialog.DontUseNativeDialog
        )

        if folder_path:
            self.pathSaveLineEdit.setText(folder_path)

    def show_date_picker(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择日期")
        dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        dialog.setModal(True)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(True)
        # 可选：默认选中今天
        calendar.setSelectedDate(QDate.currentDate())
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(lambda: self.on_date_selected(calendar, dialog))
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(calendar)
        layout.addWidget(ok_btn)
        
        dialog.resize(320, 280)
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
            self.msg.warning(self.msg, "Error", "无效目录路径")
            return

        self.localListWidget.clear()
        files = [f for f in os.listdir(self.directory) if os.path.isfile(os.path.join(self.directory, f))]
        # Filter for data files, e.g., .csv or .db; assuming .csv for now.
        data_files = [f for f in files if f.endswith('.csv')]  # Change to '.db' for SQLite
        if self.DateCheck.isChecked():
            date = '_'.join(self.DateLabel.text().split("-"))
            data_files[:] = [f for f in data_files if f.startswith("localsave_") and f[10:20] == date]
        if not data_files:
            self.msg.information(self.msg, "Info", "无数据记录")
            return

        self.localListWidget.addItems(data_files)
    
    def plotData(self):
        selected_items = self.localListWidget.selectedItems()
        if not selected_items:
            self.msg.information(self.msg, "Info", "未选中数据")
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

                space = 10
                self.DataPreview_tab.setRowCount(len(dataList[0])+space)
                self.DataPreview_tab.setColumnCount(len(dataList)+space)
                self.DataPreview_tab.setHorizontalHeaderLabels(['时间',*total_names,*['' for x in range(space)]])

                previewDataList = [list(map(str,x)) for x in dataList]
                previewDataList[0] = list(map(lambda x:time.strftime("%Y-%m-%d %H:%M:%S",x), map(time.localtime,map(eval,previewDataList[0]))))

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

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dialog = QFileDialog()
        self.dialog.setWindowTitle("请选择文件夹")
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
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)

        dataNames = ["AX","AY","AZ","GX","GY","GZ","CO2","TVOC","温度","湿度","压强"]
        valueNames = ['平均值','中位数','标准差']
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
            data_mean = list(map(lambda x: "{:.2f}".format(sum(x)/len(x)), dataList))
            data_median = list(map(lambda x: "{:.2f}".format((x[len(x)//2-1]+x[len(x)//2])/2) if len(x)%2==0 else "{:.2f}".format(x[(len(x)-1)//2]),list(map(sorted, dataList))))
            data_std = list(map(lambda mean,data: "{:.2f}".format((sum((x-eval(mean))**2 for x in data)/len(data))**(1/2)), data_mean, dataList))
            data_list = [data_mean,data_median,data_std]
            for column,value in enumerate(data_list):
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

        self.clearBtn = QPushButton()
        self.clearBtn.setText("清空")
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
        self.LogLevelLabel.setText(f'日志报告等级：{self.levelNames[self.LogLevel]}')

    def clearText(self):
        self.textedit.clear()

    def append_log(self, log: str, level: int):
        if level <= self.LogLevel:
            self.textedit.append(log)