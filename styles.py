HOMEPAGE_STYLE = """
/* 主窗口背景 */
QWidget {
    background-color: #1e1e28;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 11pt;
}

/* 左侧传感器列表滚动区域 */
QScrollArea {
    background-color: #252534;
    border-radius: 10px;
    border: 1px solid #444;
}

/* 左侧列表 */
QListWidget {
    background-color: transparent;
    border: none;
    padding: 4px;
    color: #e0e0e0;
}

QListWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
}

QListWidget::item:selected {
    background-color: #4a90e2;
    color: #ffffff;
}

/* StackWidget页面容器 */
QStackedWidget {
    background-color: #252534;
    border-radius: 10px;
    border: 1px solid #444;
}

/* 输入框 */
QLineEdit {
    background-color: #2a2a3b;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 4px 6px;
    color: #e0e0e0;
}

QLineEdit:focus {
    border: 1px solid #4a90e2;
}

/* 按钮 */
QPushButton {
    background-color: #40404a;
    color: #e0e0e0;
    border-radius: 6px;
    padding: 4px 10px;
}

QPushButton:hover {
    background-color: #50505a;
}

QPushButton:pressed {
    background-color: #38383f;
}

/* 工具按钮 */
QToolButton#toolButton {
    background-color: #40404a;
    color: #e0e0e0;
    border-radius: 6px;
    padding: 2px;
    font-weight: 600;
}

QToolButton#toolButton:hover {
    background-color: #50505a;
}

QToolButton#toolButton:pressed {
    background-color: #38383f;
}

/* 分隔条 */
QSplitter::handle {
    background-color: #3a3a4a;
    width: 6px;
    height: 6px;
}
QSplitter::handle:hover {
    background-color: #4a4a6a;
}

/* 标签页TabWidget */
QTabWidget::pane {
    border: 1px solid #444;
    border-radius: 8px;
    background-color: #252534;
}

QTabBar::tab {
    background: #2a2a3b;
    color: #e0e0e0;
    padding: 6px 12px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #4a90e2;
    color: #ffffff;
}
"""

sensor_display_stylesheet = """
/* 卡片背景 */
QFrame {
    background-color: #2c2c34;
    border-radius: 12px;
    border: 1px solid #444;
    padding: 8px;
}

/* 通用文字 */
QLabel {
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

/* 数值 */
QLabel#valueLabel {
    font-size: 22pt;
    font-weight: 600;
    color: #ffffff;
}

/* 单位 */
QLabel#unitLabel {
    font-size: 10pt;
    color: #b0b0b0;
}

/* 名称 */
QLabel {
    font-size: 12pt;
    font-weight: 500;
    margin-bottom: 4px;
}
"""