from PySide6.QtWidgets import (QWidget, QTabWidget, QListWidget, QVBoxLayout, QTableWidget, QHBoxLayout, QLabel, 
                            QToolButton, QSpacerItem, QSizePolicy, QGridLayout, QComboBox, QPushButton, 
                            QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox, QCalendarWidget, 
                            QDialog, QStyle, QTableWidgetItem, QSplitter, QInputDialog, QScrollArea, QFrame,
                            QStackedWidget, QMenu)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal, QDate, Slot
from serial.tools import list_ports
import os, json, time

from Serial import SerialThread
from PlotWidget import SensorPlotter
from components import SensorDisplayWidget, DataModifyDialog
import styles

class Homepage(QWidget):
    sendTextSignal = Signal(str)
    sendErrorSignal = Signal(str)
    sensor_config = {}  # 用于存储传感器配置数据

    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setStyleSheet(HOMEPAGE_STYLE)

        self.dataBuffer = []
        self.pathSave = "history"
        self.anims: dict[str, QPropertyAnimation | None] = {"Sensor":None}  # 用于存储动画对象
        self.settingExpanded = False  # 记录设置面板的展开状态
        self.sensorDisplay = True
        self.runtimeSave = None

        self.initUI()

    def initUI(self):
        # ----------------- 主布局 -----------------
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ----------------- 左侧监测部分 -------------------
        left_main_vertical = QVBoxLayout()
        main_layout.addLayout(left_main_vertical, stretch=4)
        # ----------------- 左右可拖拽分隔 -----------------
        horizontal_splitter = QSplitter(Qt.Horizontal)
        left_main_vertical.addWidget(horizontal_splitter, 1)

        # ----------------- 左侧滚动区域（选择传感器） -----------------
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # 传感器列表
        self.sensor_list = QListWidget()
        self.sensor_list.currentRowChanged.connect(self._on_sensor_selection_changed)

        left_layout.addWidget(self.sensor_list)
        left_scroll.setWidget(left_content)

        horizontal_splitter.addWidget(left_scroll)
        horizontal_splitter.setStretchFactor(0, 3)  # 左侧占比

        # ----------------- 右侧区域（StackedWidget） -----------------
        self.right_stack = QStackedWidget()
        horizontal_splitter.addWidget(self.right_stack)
        horizontal_splitter.setStretchFactor(1, 10)  # 右侧占比

        # 左侧监测部分--最下方命令输入行
        leftdown_horizontal = QHBoxLayout()
        self.sendline = QLineEdit()
        self.sendline.setPlaceholderText("输入命令并按回车发送")
        self.sendlineButton = QPushButton("发送")
        self.sendline.returnPressed.connect(self.sendText)
        self.sendlineButton.clicked.connect(self.sendText)
        leftdown_horizontal.addWidget(self.sendline)
        leftdown_horizontal.addWidget(self.sendlineButton)
        left_main_vertical.addLayout(leftdown_horizontal)

        # 设置面板
        self.command_panel = CommandPanel()  # 直接使用 SettingsPage 作为右侧设置面板
        self.command_panel.setFixedWidth(0)  # 初始宽度为0，表示收起状态
        main_layout.addWidget(self.command_panel)

        # 工具按钮
        self.toolButton = QToolButton(self)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setStyleSheet("* {background-color: #404040}")
        self.toolButton.setText("设\n置")
        self.toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolButton.setArrowType(Qt.DownArrow)
        sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toolButton.setSizePolicy(sp)
        self.toolButton.clicked.connect(self._toggleSettingPanel)
        main_layout.addWidget(self.toolButton)

        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.update_sensor_config(self.sensor_config)

    def sendText(self):
        try:
            if self.command_panel.serState:
                data = self.sendline.text()
                self.sendTextSignal.emit(f"发送: {data}")
                if self.command_panel.sendMode.isChecked():
                    if all(c in "0123456789abcdefABCDEF " for c in data):
                        data_bytes = bytes.fromhex(data)
                        self.command_panel.serThread.serial.write(data_bytes)
                    else:
                        raise Exception("非十六进制字符串")
                else:
                    self.command_panel.serThread.serial.write(data.encode('utf-8'))
                #self.sendline.setText("")
            else:
                self.sendTextSignal.emit("尚未连接")
                self.sendline.setText("")
        except Exception as e:
            self.sendErrorSignal.emit(str(e))

    def updateDataDisplay(self,dataText:str):
        try:
            pass
        except Exception as e:
            self.command_panel.serLogSignal.emit(f"错误：{e}")

    def clearData(self):
        pass

    def _toggleSettingPanel(self):
        startWidth = self.command_panel.width()
        if self.settingExpanded:
            # 收起设置面板
            self._animateWidgetDisplay("Command", startWidth,0,self.command_panel,"maximumWidth")
            self.toolButton.setArrowType(Qt.DownArrow)
        else:
            # 展开设置面板
            self._animateWidgetDisplay("Command", startWidth,300,self.command_panel,"maximumWidth")
            self.toolButton.setArrowType(Qt.LeftArrow)
        self.settingExpanded = not self.settingExpanded

    def _animateWidgetDisplay(self, anime, start, end, widget, property, duration=200):
        self.anims[anime] = QPropertyAnimation(widget, bytes(property,encoding='utf-8'))
        self.anims[anime].setDuration(duration)
        self.anims[anime].setStartValue(start)
        self.anims[anime].setEndValue(end)
        self.anims[anime].start()

    def update_sensor_config(self, sensor_config: dict):
        self.sensor_config = sensor_config
         # 清空左侧列表和右侧Stack
        self.sensor_list.clear()
        self._clear_stacked_widget()
        
        for idx,(sensor, data_list) in enumerate(sensor_config.items()):
            self.sensor_list.addItem(f"{sensor}")
            page = self._create_sensor_page(data_list)
            self.right_stack.addWidget(page)

    def on_sensor_config_updated(self):
        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.update_sensor_config(self.sensor_config)
    
    def _create_sensor_page(self, data_list: list):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(5)

        # 右侧上下分割器
        vertical_splitter = QSplitter(Qt.Vertical)
        page_layout.addWidget(vertical_splitter)

        # 上部滚动区 + 网格布局
        top_scroll = QScrollArea()
        top_scroll.setWidgetResizable(True)
        top_content = QWidget()
        top_layout = QGridLayout(top_content)
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_layout.setSpacing(10)
        self._add_data_grid(data_list, top_layout)
        top_scroll.setWidget(top_content)
        vertical_splitter.addWidget(top_scroll)

        # 下部滚动区 + TabWidget
        bottom_scroll = QScrollArea()
        bottom_scroll.setWidgetResizable(True)
        bottom_content = QWidget()
        bottom_layout = QVBoxLayout(bottom_content)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(5)

        tab_widget = QTabWidget()
        # 图像页
        image_page = QLabel("图像区域")
        image_page.setAlignment(Qt.AlignCenter)
        tab_widget.addTab(image_page, "图像")

        # 统计页
        stats_page = QLabel("统计数值区域")
        stats_page.setAlignment(Qt.AlignCenter)
        tab_widget.addTab(stats_page, "统计")

        bottom_layout.addWidget(tab_widget)
        bottom_scroll.setWidget(bottom_content)
        vertical_splitter.addWidget(bottom_scroll)
        vertical_splitter.setStretchFactor(0, 1)
        vertical_splitter.setStretchFactor(1, 8)

        return page

    def _add_data_grid(self, data_list: list, layout: QGridLayout):
        for i, data in enumerate(data_list):
            data_card = SensorDisplayWidget(data)
            row = i // 3
            col = i % 3
            layout.addWidget(data_card, row, col)

    def _clear_stacked_widget(self):
        while self.right_stack.count() > 0:
            widget = self.right_stack.widget(0)
            self.right_stack.removeWidget(widget)
            widget.deleteLater()

    @Slot(int)
    def _on_sensor_selection_changed(self, current_row):
        if current_row >= 0 and current_row < self.right_stack.count():
            self.right_stack.setCurrentIndex(current_row)
    
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
        # self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton("设置")
        self.sendMode = QCheckBox("发送Bytes")
        self.TextCopy = QTextEdit()
        self.TextCopy.setReadOnly(True)
        

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
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存

        self.gridlayout.addWidget(self.sendMode, 3, 1)
        self.sendMode.setChecked(True)

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
                total_names = ['温度','湿度','压强','LIGHT','CO2','TVOC']
                bh_dist = {'LIGHT':{'times':[],'values':[]}}
                gas_dist = {'CO2':{'times':[],'values':[]},'TVOC':{'times':[],'values':[]}}
                thp_dist = {'温度':{'times':[],'values':[]},'湿度':{'times':[],'values':[]},'压强':{'times':[],'values':[]}}
                for line in f:
                    #dataList.append(list(map(eval, line.strip().split(','))))
                    dataList.append([float(x) for x in line.strip().split(',')])
                dataList = list(zip(*dataList))
                for i, name in enumerate(total_names):
                    if i < 3:
                        thp_dist[name]['times'] = dataList[0]
                        thp_dist[name]['values'] = dataList[i+1]
                    elif i < 4:
                        bh_dist[name]['times'] = dataList[0]
                        bh_dist[name]['values'] = dataList[i+1]
                    elif i > 4:
                        gas_dist[name]['times'] = dataList[0]
                        gas_dist[name]['values'] = dataList[i+1]
                    

                self.RegionPlot.load_bh_history(bh_dist)
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
    sensor_config_changed = Signal()

    tmpConfig = {}  # 临时配置字典，用于存储当前设置
    sensor_config = {}  # 存储传感器配置的字典

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

        self.main_layout = QVBoxLayout(self)
        self.tabWidget = QTabWidget()
        self.main_layout.addWidget(self.tabWidget)
    
        tab_sensor = QWidget()
        tab_sensor_layout = QGridLayout(tab_sensor)
        tab_custom = QWidget()
        tab_custom_layout = QGridLayout(tab_custom)

        self.tabWidget.addTab(tab_sensor,"数据设置")
        self.tabWidget.addTab(tab_custom,"界面设置")
        
        #############
        # 数据设置页 #
        #############
        pathLabel = QLabel("数据保存目录")
        self.pathLineEdit = QLineEdit()
        nowDir = os.getcwd()
        self.pathLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton()
        self.browserFileBtn.setText("浏览...")
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtn = QPushButton()
        self.pathBtn.setText("设置")
        self.pathBtn.clicked.connect(self.on_pathBtn_click)
        tab_sensor_layout.addWidget(pathLabel,0,0)
        tab_sensor_layout.addWidget(self.pathLineEdit,1,0)
        tab_sensor_layout.addWidget(self.browserFileBtn,1,1)
        tab_sensor_layout.addWidget(self.pathBtn,1,2)
        
        # 配置传感器类型和数据格式等设置项（可扩展）
        self.action_hbox = QHBoxLayout()
        self.action_add_btn = QPushButton("添加传感器")
        self.action_remove_btn = QPushButton("移除当前传感器")
        self.action_add_data_btn = QPushButton("添加数据项")
        self.action_remove_data_btn = QPushButton("移除当前数据项")
        self.action_reset_btn = QPushButton("重置配置")
        self.action_clear_btn = QPushButton("清除配置")
        self.action_hbox.addWidget(self.action_add_btn)
        self.action_hbox.addWidget(self.action_remove_btn)
        self.action_hbox.addWidget(self.action_add_data_btn)
        self.action_hbox.addWidget(self.action_remove_data_btn)
        self.action_hbox.addWidget(self.action_reset_btn)
        self.action_hbox.addWidget(self.action_clear_btn)
        tab_sensor_layout.addLayout(self.action_hbox,2,0,1,3)

        self.splitter = QSplitter(Qt.Horizontal)
        self.sensor_list = QListWidget()
        self.data_list = QListWidget()
        self.splitter.addWidget(self.sensor_list)
        self.splitter.addWidget(self.data_list)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        tab_sensor_layout.addWidget(self.splitter,3,0,1,3)
        # ------------------------ 在初始化 UI 中添加右键菜单 ------------------------
        self.sensor_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sensor_list.customContextMenuRequested.connect(self.show_sensor_context_menu)
        self.sensor_list.setDragDropMode(QListWidget.InternalMove)  # 支持拖动排序
        self.sensor_list.setDefaultDropAction(Qt.MoveAction)
        self.sensor_list.model().rowsMoved.connect(self.sensor_rows_moved)

        self.action_apply_btn = QPushButton("应用配置")
        tab_sensor_layout.addWidget(self.action_apply_btn,4,0,1,3)

        tab_sensor_layout.setRowStretch(3,8)
        tab_sensor_layout.setRowStretch(6,1)

        # 信号绑定
        self.action_add_btn.clicked.connect(self.add_sensor)
        self.action_remove_btn.clicked.connect(self.del_sensor)
        self.action_add_data_btn.clicked.connect(self.add_data)
        self.action_remove_data_btn.clicked.connect(self.del_data)
        self.action_reset_btn.clicked.connect(self.reset_config)
        self.action_clear_btn.clicked.connect(self.clear_config)
        self.action_apply_btn.clicked.connect(self.save_config)

        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.tmpConfig = self.sensor_config.copy()
                self.update_display()

        #############
        # 界面设置页 #
        #############
        self.styleCombobox = QComboBox()
        style_dict = styles.material_styles_dict
        self.styleCombobox.addItems(style_dict.keys())
        self.styleApply = QPushButton("应用")
        self.styleApply.clicked.connect(lambda:self.styleSignal.emit(style_dict[self.styleCombobox.currentText()]))
        tab_custom_layout.addWidget(self.styleCombobox,2,0)
        tab_custom_layout.addWidget(self.styleApply,2,1)
        
        tab_custom_layout.setColumnStretch(0,1)
        tab_custom_layout.setRowStretch(3,1)

    def on_pathBtn_click(self):
        directory = self.pathLineEdit.text().strip()
        self.pathSaveSignal.emit(directory)

    ############ 动态传感器配置 ##################
    # ------------------------ 功能实现 ------------------------
    def add_sensor(self):
        name, ok = QInputDialog.getText(self, "增加传感器", "输入传感器名称:")
        if ok and name.strip():
            if name in self.tmpConfig:
                QMessageBox.warning(self, "错误", "传感器已存在")
                return
            self.tmpConfig[name] = []
            self.update_display()

    def del_sensor(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "没有传感器可删除")
            return
        sensor, ok = QInputDialog.getItem(self, "删除传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            self.tmpConfig.pop(sensor)
            self.update_display()

    def add_data(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "请先添加传感器")
            return
        # 选择传感器
        sensor, ok = QInputDialog.getItem(self, "选择传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            # 输入数据名字
            data_name, ok_name = QInputDialog.getText(self, "数据名字", "输入数据名称:")
            if ok_name and data_name.strip():
                # 输入单位
                unit, ok_unit = QInputDialog.getText(self, "数据单位", "输入单位:")
                if ok_unit:
                    entry = {"name": data_name, "unit": unit}
                    self.tmpConfig[sensor].append(entry)
                    self.update_display()

    def del_data(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "没有数据可删除")
            return
        # 选择传感器
        sensor, ok = QInputDialog.getItem(self, "选择传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            if not self.tmpConfig[sensor]:
                QMessageBox.warning(self, "提示", "该传感器没有数据可删除")
                return
            # 选择数据
            data, ok_data = QInputDialog.getItem(self, "删除数据", "选择数据:", [f"{d['name']} ({d['unit']})" for d in self.tmpConfig[sensor]], 0, False)
            if ok_data:
                data = {"name": data.split(" (")[0], "unit": data.split(" (")[1][:-1]}  # 解析出名字和单位
                self.tmpConfig[sensor].remove(data)
                self.update_display()

    def reset_config(self):
        self.tmpConfig = self.sensor_config.copy()
        self.update_display()

    def clear_config(self):
        self.tmpConfig.clear()
        self.update_display()

    def save_config(self):
        self.sensor_config = {k: v.copy() for k, v in self.tmpConfig.items()}
        with open("sensor_config.json", "w", encoding="utf-8") as f:
            json.dump(self.sensor_config, f, ensure_ascii=False, indent=4)
        self.sensor_config_changed.emit()
        QMessageBox.information(self, "保存成功", "配置已保存")
    
    # ------------------------ 右键菜单实现 ------------------------
    # ------------------------ 新增方法 ------------------------
    def show_sensor_context_menu(self, pos):
        item = self.sensor_list.itemAt(pos)
        if item is None:
            return

        menu = QMenu()
        rename_action = menu.addAction("重命名传感器")
        delete_action = menu.addAction("删除传感器")
        modify_action = menu.addAction("修改数据")  # 修改为批量修改
        action = menu.exec(self.sensor_list.mapToGlobal(pos))

        if action == rename_action:
            self.rename_sensor(item)
        elif action == delete_action:
            self.delete_sensor(item)
        elif action == modify_action:
            self.modify_data_dialog()

    def rename_sensor(self, item):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "重命名传感器", "输入新名称:", text=old_name)
        if ok and new_name.strip():
            if new_name in self.tmpConfig:
                QMessageBox.warning(self, "错误", "该名称已存在")
                return
            # 先保存顺序
            keys = list(self.tmpConfig.keys())
            values = list(self.tmpConfig.values())
            index = keys.index(old_name)
            # 修改键名
            keys[index] = new_name
            # 重建字典
            self.tmpConfig = dict(zip(keys, values))
            self.update_display()

    def delete_sensor(self, item):
        name = item.text()
        reply = QMessageBox.question(self, "确认删除", f"确定删除传感器 {name} 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tmpConfig.pop(name)
            self.update_display()
    
    def modify_data_dialog(self):
        # 找到当前传感器
        sensor_row = self.sensor_list.currentRow()
        if sensor_row < 0:
            QMessageBox.warning(self, "提示", "请选择一个传感器")
            return
        sensor = self.sensor_list.item(sensor_row).text()
        dialog = DataModifyDialog(self, sensor, self.tmpConfig[sensor])
        if dialog.exec() == QDialog.Accepted:
            # 更新 tmpConfig
            self.tmpConfig[sensor] = dialog.data_list
            self.update_display()

    # ------------------------ 拖动排序实现 ------------------------
    def sensor_rows_moved(self, parent, start, end, destination, row):
        # 根据 QListWidget 的顺序重新排列 tmpConfig
        new_order = [self.sensor_list.item(i).text() for i in range(self.sensor_list.count())]
        # 用列表重建 tmpConfig 顺序
        self.tmpConfig = {k: self.tmpConfig[k] for k in new_order}
        self.update_display()

    # ------------------------ 更新显示 ------------------------
    def update_display(self):
        self.sensor_list.clear()
        self.data_list.clear()
        for sensor, data_list in self.tmpConfig.items():
            self.sensor_list.addItem(sensor)
            self.data_list.addItem(", ".join([f"{data['name']} ({data['unit']})" for data in data_list]))



    #############################################
    
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

        dataNames = ["温度","湿度","压强","LIGHT","CO2","TVOC",]
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