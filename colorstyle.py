
dark_theme_colors = {
    "Background" : "#121212",
    "Surface" : "#1E1E1E",
    "Text_Primary" : "#E0E0E0",
    "Text_Secondary" : "#A0A0A0",
    "Accent" : "#BB86FC",  # 柔和紫
    "Border_Hover" :  "#333333"
}

light_theme_colors = {
    "Background" : "#FFFFFF",
    "Surface" : "#C8C8C8",
    "Text_Primary" : "#000000",
    "Text_Secondary" : "#606060",
    "Accent" : "#6200EE",  # 深紫
    "Border_Hover" :  "#CCCCCC"
}

# 颜色配置文件路径
import json
import os

CONFIG_DIR = "config"
DARK_THEME_CONFIG = os.path.join(CONFIG_DIR, "dark_theme_colors.json")
LIGHT_THEME_CONFIG = os.path.join(CONFIG_DIR, "light_theme_colors.json")

def ensure_config_dir():
    """确保配置目录存在"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

def save_theme_colors(is_dark: bool, colors: dict):
    """保存主题颜色到文件"""
    ensure_config_dir()
    config_file = DARK_THEME_CONFIG if is_dark else LIGHT_THEME_CONFIG
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(colors, f, indent=4, ensure_ascii=False)
    # 更新全局变量
    if is_dark:
        global dark_theme_colors
        dark_theme_colors = colors
    else:
        global light_theme_colors
        light_theme_colors = colors

def load_theme_colors():
    """从文件加载主题颜色，如果不存在则使用默认值"""
    global dark_theme_colors, light_theme_colors
    
    if os.path.exists(DARK_THEME_CONFIG):
        with open(DARK_THEME_CONFIG, 'r', encoding='utf-8') as f:
            dark_theme_colors = json.load(f)
    
    if os.path.exists(LIGHT_THEME_CONFIG):
        with open(LIGHT_THEME_CONFIG, 'r', encoding='utf-8') as f:
            light_theme_colors = json.load(f)

def reset_theme_colors(is_dark: bool):
    """重置主题颜色为默认值"""
    if is_dark:
        default_colors = {
            "Background" : "#121212",
            "Surface" : "#1E1E1E",
            "Text_Primary" : "#E0E0E0",
            "Text_Secondary" : "#A0A0A0",
            "Accent" : "#BB86FC",
            "Border_Hover" :  "#333333"
        }
    else:
        default_colors = {
            "Background" : "#FFFFFF",
            "Surface" : "#C8C8C8",
            "Text_Primary" : "#000000",
            "Text_Secondary" : "#606060",
            "Accent" : "#6200EE",
            "Border_Hover" :  "#CCCCCC"
        }
    save_theme_colors(is_dark, default_colors)
    return default_colors

# 获取当前主题颜色
def get_theme_colors(is_dark: bool = True):
    """返回当前主题的颜色字典"""
    return dark_theme_colors if is_dark else light_theme_colors

# Menubar样式表生成
def get_menubar_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"""
        background: {colors['Surface']};
    """

def get_menubar_title_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"color: {colors['Text_Primary']}; font-size: 16px; padding-left: 10px;"

def get_menubar_button_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"""
        QPushButton {{
            color: {colors['Text_Primary']};
            background: transparent;
            border: None;
            font-size: 20px;
            padding: 1px;
        }}
        QPushButton:hover {{
            background: {colors['Border_Hover']};
        }}
    """

# Sidebar样式表生成
def get_sidebar_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"background-color: {colors['Surface']};"

def get_sidebar_button_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    if is_dark:
        bg_normal = "#2c3e50"
        bg_hover = "#34495e"
        bg_checked = "#3498db"
    else:
        bg_normal = "#A0A0A0"
        bg_hover = "#B0B0B0"
        bg_checked = "#6200EE"
    
    return f"""
        SidebarButton {{
            background-color: {bg_normal};
            color: {colors['Text_Primary']};
            border: none;
            font-weight: bold;
            font-size: 18px;
            text-align: center;
            icon-size: 30px;
        }}
        SidebarButton:hover {{
            background-color: {bg_hover};
        }}
        SidebarButton:checked {{
            background-color: {bg_checked};
        }}
    """

# Homepage样式表生成
def get_homepage_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"""
        background-color: {colors['Surface']};
        color: {colors['Text_Primary']};
    """

def get_homepage_label_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"background-color: {colors['Surface']};"

def get_homepage_sensor_label_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"""
        QLabel[text~="MPU6050"], QLabel[text~="气体传感器"], QLabel[text~="温湿压传感器"]
        {{
            background-color: {colors['Surface']};
            border: 1px solid {colors['Border_Hover']};
            border-radius: 4px;
            color: {colors['Text_Primary']};
            font-weight: bold;
        }}
    """

def get_tool_button_stylesheet(is_dark: bool = True):
    colors = get_theme_colors(is_dark)
    return f"* {{background-color: {colors['Surface']}}}"