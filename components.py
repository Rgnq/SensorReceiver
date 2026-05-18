from PySide6.QtWidgets import (QLabel, QVBoxLayout, QHBoxLayout, QFrame, QDialog, QTableWidget, 
                               QTableWidgetItem, QPushButton, QLineEdit, QHeaderView, QInputDialog)

from PySide6.QtCore import Qt

from styles import sensor_display_stylesheet

class SensorDisplayWidget(QFrame):
    def __init__(self, sensor_info: dict, parent=None):
        """
        sensor_info 示例: {"name": "温度", "unit": "℃"}
        """
        super().__init__(parent)

        self.sensor_name = sensor_info.get("name", "未知传感器")
        self.sensor_unit = sensor_info.get("unit", "")
        self.sensor_value = 0  # 初始值

        # 设置 QFrame 样式，类似卡片风格
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(sensor_display_stylesheet)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)

        # 传感器名称
        self.name_label = QLabel(self.sensor_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.name_label)

        # 水平布局: 数值 + 单位
        value_layout = QHBoxLayout()
        value_layout.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(str(self.sensor_value))
        self.value_label.setObjectName("valueLabel")
        self.unit_label = QLabel(self.sensor_unit)
        self.unit_label.setObjectName("unitLabel")

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.unit_label)

        main_layout.addLayout(value_layout)
        self.setLayout(main_layout)

    def set_value(self, value):
        """更新传感器数值"""
        self.sensor_value = value
        self.value_label.setText(str(value))

class DataModifyDialog(QDialog):
    def __init__(self, parent, sensor, data_list):
        super().__init__(parent)
        self.setWindowTitle(f"修改数据 - {sensor}")
        self.resize(500, 400)
        self.sensor = sensor
        # 深拷贝原数据，防止直接修改
        self.data_list = [d.copy() for d in data_list]

        self.current_page = 0
        self.page_size = 5  # 每页显示5条

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["数据名称", "单位", "操作"])
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)  # 自动调整大小
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)         # 第一列自适应拉伸
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 第二列自适应内容
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 第三列自适应内容
        self.table.horizontalHeader().setStretchLastSection(True)  # 最后一列填充剩余空间
        self.table.verticalHeader().setVisible(False)  # 可选：隐藏行号
        self.layout.addWidget(self.table, 1)

        # 翻页按钮
        page_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.next_btn)
        self.layout.addLayout(page_layout)

        add_btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("新增数据")
        add_btn_layout.addWidget(self.add_btn)
        self.layout.insertLayout(1, add_btn_layout)  # 插入到表格下方、编辑区上方

        # 编辑区
        edit_layout = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.unit_edit = QLineEdit()
        self.apply_btn = QPushButton("应用修改")
        edit_layout.addWidget(QLabel("名称:"))
        edit_layout.addWidget(self.name_edit)
        edit_layout.addWidget(QLabel("单位:"))
        edit_layout.addWidget(self.unit_edit)
        edit_layout.addWidget(self.apply_btn)
        self.layout.addLayout(edit_layout)

        # 完成按钮
        self.finish_btn = QPushButton("完成")
        self.layout.addWidget(self.finish_btn)

        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        self.apply_btn.clicked.connect(self.apply_edit)
        self.finish_btn.clicked.connect(self.accept)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.add_btn.clicked.connect(self.add_data)

        self.selected_row = None
        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)
        start = self.current_page * self.page_size
        end = min(len(self.data_list), start + self.page_size)
        for i, data in enumerate(self.data_list[start:end]):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(data["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(data["unit"]))

            # 删除按钮
            btn = QPushButton("删除")
            btn.clicked.connect(lambda _, row=i: self.delete_row(row))
            self.table.setCellWidget(i, 2, btn)

    def add_data(self):
        # 弹出输入对话框输入新数据名称和单位
        name, ok_name = QInputDialog.getText(self, "新增数据", "输入数据名称:")
        if not (ok_name and name.strip()):
            return

        unit, ok_unit = QInputDialog.getText(self, "新增数据", "输入单位:")
        if not ok_unit:
            return

        # 将新数据添加到 data_list
        self.data_list.append({"name": name.strip(), "unit": unit.strip()})
        # 如果当前页已经满5条，自动跳到最后一页显示新数据
        self.current_page = (len(self.data_list) - 1) // self.page_size
        self.update_table()

    def delete_row(self, row):
        real_index = self.current_page * self.page_size + row
        if real_index < len(self.data_list):
            self.data_list.pop(real_index)
            self.update_table()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.data_list):
            self.current_page += 1
            self.update_table()

    def on_cell_clicked(self, row, column):
        # 选中行，加载到编辑区
        real_index = self.current_page * self.page_size + row
        if real_index < len(self.data_list):
            self.selected_row = real_index
            data = self.data_list[real_index]
            self.name_edit.setText(data["name"])
            self.unit_edit.setText(data["unit"])

    def apply_edit(self):
        if self.selected_row is None:
            return
        new_name = self.name_edit.text().strip()
        new_unit = self.unit_edit.text().strip()
        if new_name:
            self.data_list[self.selected_row]["name"] = new_name
        if new_unit:
            self.data_list[self.selected_row]["unit"] = new_unit
        self.update_table()