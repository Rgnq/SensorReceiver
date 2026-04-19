"""
国际化（i18n）模块 - 提供多语言支持
支持开发模式和 Nuitka 打包模式
"""
import json
import os
import sys
import shutil
from typing import Dict, Any
from pathlib import Path

# 翻译数据存储
_translations = {}
_current_language = "zh_CN"
_supported_languages = {
    "zh_CN": "简体中文",
    "en_US": "English"
}

# 检测运行环境和资源路径
def _get_base_path():
    """获取应用程序的基础路径
    
    支持两种模式：
    1. 开发模式：使用项目目录
    2. Nuitka 打包模式：优先使用可执行文件目录，如果没有i18n目录则使用打包内资源
    """
    if getattr(sys, 'frozen', False):
        # 打包模式
        exe_dir = os.path.dirname(sys.executable)
        
        # 检查可执行文件目录是否有i18n目录，如果有则优先使用外部文件
        if os.path.exists(os.path.join(exe_dir, "i18n")):
            return exe_dir
        
        # 否则使用打包内的资源
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller
            return sys._MEIPASS
        else:
            # Nuitka 或其他
            return exe_dir
    else:
        # 开发模式：使用脚本所在目录
        return os.path.dirname(os.path.abspath(__file__))

_BASE_PATH = _get_base_path()
I18N_DIR = os.path.join(_BASE_PATH, "i18n")
LANGUAGE_CONFIG = os.path.join(_BASE_PATH, "config", "language.json")


def _get_packaged_i18n_path():
    """获取打包内的i18n路径（用于fallback）"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller
        return os.path.join(sys._MEIPASS, "i18n")
    elif getattr(sys, 'frozen', False):
        # Nuitka - 资源应该在exe_dir，但如果没有外部覆盖，则可能不存在
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, "i18n")
    else:
        # 开发模式
        return I18N_DIR


def ensure_i18n_dir():
    """确保i18n目录存在"""
    # 确保配置目录存在
    config_dir = os.path.dirname(LANGUAGE_CONFIG)
    os.makedirs(config_dir, exist_ok=True)
    
    # 检查i18n目录是否存在
    if not os.path.exists(I18N_DIR):
        # 在打包模式中，如果不存在则尝试创建
        os.makedirs(I18N_DIR, exist_ok=True)


def load_language(language_code: str):
    """加载指定语言的翻译文件"""
    global _current_language, _translations
    
    ensure_i18n_dir()
    language_file = os.path.join(I18N_DIR, f"{language_code}.json")
    
    # 首先尝试从当前BASE_PATH加载
    if os.path.exists(language_file):
        try:
            with open(language_file, 'r', encoding='utf-8') as f:
                _translations = json.load(f)
                _current_language = language_code
                save_language_preference(language_code)
                return True
        except Exception as e:
            print(f"Error loading language file {language_file}: {e}")
    
    # 如果不存在，尝试从打包内路径加载（fallback）
    packaged_i18n_dir = _get_packaged_i18n_path()
    if packaged_i18n_dir != I18N_DIR:
        packaged_file = os.path.join(packaged_i18n_dir, f"{language_code}.json")
        if os.path.exists(packaged_file):
            try:
                with open(packaged_file, 'r', encoding='utf-8') as f:
                    _translations = json.load(f)
                    _current_language = language_code
                    save_language_preference(language_code)
                    return True
            except Exception as e:
                print(f"Error loading packaged language file {packaged_file}: {e}")
    
    return False


def get_current_language():
    """获取当前语言代码"""
    return _current_language


def get_language_name(language_code: str = None):
    """获取语言的显示名称"""
    if language_code is None:
        language_code = _current_language
    return _supported_languages.get(language_code, language_code)


def get_supported_languages():
    """获取所有支持的语言"""
    return _supported_languages.copy()


def t(key: str, *args, **kwargs) -> str:
    """
    翻译函数 - 获取翻译后的字符串
    
    Args:
        key: 翻译键，使用点号分隔的路径 (e.g., "page.homepage.title")
        *args: 用于格式化的位置参数
        **kwargs: 用于格式化的关键字参数
    
    Returns:
        翻译后的字符串，如果键不存在则返回键本身
    """
    try:
        # 通过点号路径获取嵌套字典的值
        keys = key.split('.')
        value = _translations
        for k in keys:
            value = value[k]
        
        # 如果有格式化参数，进行格式化
        if args or kwargs:
            return value.format(*args, **kwargs)
        return str(value)
    except (KeyError, TypeError):
        # 如果找不到翻译，返回键本身
        return key


def set_language(language_code: str) -> bool:
    """设置当前语言"""
    if language_code in _supported_languages:
        return load_language(language_code)
    return False


def load_language_preference():
    """从配置文件加载语言偏好"""
    global _current_language
    
    if os.path.exists(LANGUAGE_CONFIG):
        try:
            with open(LANGUAGE_CONFIG, 'r', encoding='utf-8') as f:
                config = json.load(f)
                language = config.get('language', 'zh_CN')
                if language in _supported_languages:
                    _current_language = language
                    load_language(language)
                    return
        except Exception as e:
            print(f"Error loading language preference: {e}")
    
    # 默认加载中文
    load_language('zh_CN')


def save_language_preference(language_code: str):
    """保存语言偏好到配置文件"""
    os.makedirs("config", exist_ok=True)
    config = {'language': language_code}
    try:
        with open(LANGUAGE_CONFIG, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving language preference: {e}")


def initialize_i18n():
    """初始化i18n系统 - 在应用启动时调用"""
    ensure_i18n_dir()
    create_default_translations()
    load_language_preference()


def create_default_translations():
    """创建默认的翻译文件"""
    # 中文翻译
    zh_translations = {
        "page": {
            "homepage": {
                "title": "首页",
                "mpu6050": "MPU6050",
                "gas_sensor": "气体传感器",
                "thp_sensor": "温湿压传感器",
                "plot_toggle": "显示/隐藏图表",
                "plot_tab": "图像",
                "analysis_tab": "统计",
                "command_input": "输入命令并按回车发送",
                "send_button": "发送",
                "not_connected": "尚未连接",
                "ax": "加速度X",
                "ay": "加速度Y",
                "az": "加速度Z",
                "gx": "陀螺仪X",
                "gy": "陀螺仪Y",
                "gz": "陀螺仪Z",
                "co2": "CO2",
                "tvoc": "TVOC",
                "temperature": "温度",
                "humidity": "湿度",
                "pressure": "压强",
                "settings": "设\n置"
            },
            "history": {
                "title": "历史",
                "browse": "浏览...",
                "retrieve": "检索",
                "select_date": "选择日期",
                "enable": "启用",
                "select_data": "选择数据",
                "preview_data": "预览数据",
                "analyze": "分析",
                "upper_toggle": "展开/折叠 上部分",
                "lower_toggle": "展开/折叠 下部分",
                "no_data": "无数据记录",
                "no_data_selected": "未选中数据",
                "invalid_directory": "无效目录路径",
                "error_loading": "加载数据失败",
                "analysis_tab": "分析",
                "select_folder": "选择文件夹",
                "confirm": "确定"
            },
            "settings": {
                "title": "设置",
                "save_directory": "数据保存目录",
                "browse": "浏览...",
                "set": "设置",
                "material_theme": "Material主题",
                "apply": "应用",
                "custom_colors": "自定义主题颜色",
                "edit_theme": "编辑主题:",
                "dark_theme": "深色主题",
                "light_theme": "浅色主题",
                "reset_colors": "重置为默认颜色",
                "reset_success": "已重置为默认颜色",
                "language": "语言",
                "select_language": "选择语言",
                "export_language": "导出语言文件",
                "reset_message_title": "提示",
                "select_folder_title": "请选择文件夹",
                "export_dialog_title": "导出 {0} 语言文件"
            },
            "analysis": {
                "mean": "平均值",
                "median": "中位数",
                "std_dev": "标准差",
                "max": "最大值",
                "min": "最小值",
                "range": "范围"
            },
            "log": {
                "title": "日志",
                "error": "错误",
                "warning": "警告",
                "info": "信息",
                "level": "日志报告等级：",
                "toggle": "切换",
                "clear": "清空",
                "toggle_tooltip": "切换日志过滤等级"
            }
        },
        "command_panel": {
            "title": "设置",
            "select_port": "选择端口",
            "refresh": "刷新",
            "connect": "连/断",
            "baudrate": "波特率",
            "auto_save": "自动保存",
            "enable": "启用",
            "dashboard": "显示仪表盘",
            "no_ports": "无可用串口"
        },
        "color": {
            "background": "背景色",
            "surface": "表面色",
            "text_primary": "主文本色",
            "text_secondary": "副文本色",
            "accent": "强调色",
            "border_hover": "悬停边框色",
            "select_color_title": "选择{0}颜色"
        },
        "error": {
            "title": "错误",
            "error": "错误",
            "failed_to_load": "加载数据失败：",
            "export_success": "成功",
            "export_failed": "导出语言文件失败",
            "export_message": "语言文件已导出到:",
            "json_filter": "JSON 文件 (*.json)"
        }
    }
    
    # 英文翻译
    en_translations = {
        "page": {
            "homepage": {
                "title": "Home",
                "mpu6050": "MPU6050",
                "gas_sensor": "Gas Sensor",
                "thp_sensor": "Temperature & Humidity & Pressure",
                "plot_toggle": "Show/Hide Chart",
                "plot_tab": "Plot",
                "analysis_tab": "Analysis",
                "command_input": "Enter command and press Enter to send",
                "send_button": "Send",
                "not_connected": "Not connected",
                "ax": "Accel X",
                "ay": "Accel Y",
                "az": "Accel Z",
                "gx": "Gyro X",
                "gy": "Gyro Y",
                "gz": "Gyro Z",
                "co2": "CO2",
                "tvoc": "TVOC",
                "temperature": "Temperature",
                "humidity": "Humidity",
                "pressure": "Pressure",
                "settings": "S\ne\nt\nt\ni\nn\ng"
            },
            "history": {
                "title": "History",
                "browse": "Browse...",
                "retrieve": "Retrieve",
                "select_date": "Select Date",
                "enable": "Enable",
                "select_data": "Select Data",
                "preview_data": "Preview Data",
                "analyze": "Analyze",
                "upper_toggle": "Toggle Upper Section",
                "lower_toggle": "Toggle Lower Section",
                "no_data": "No data records",
                "no_data_selected": "No data selected",
                "invalid_directory": "Invalid directory path",
                "error_loading": "Failed to load data",
                "analysis_tab": "Analysis",
                "select_folder": "Select Folder",
                "confirm": "OK"
            },
            "settings": {
                "title": "Settings",
                "save_directory": "Data Save Directory",
                "browse": "Browse...",
                "set": "Set",
                "material_theme": "Material Theme",
                "apply": "Apply",
                "custom_colors": "Custom Theme Colors",
                "edit_theme": "Edit Theme:",
                "dark_theme": "Dark Theme",
                "light_theme": "Light Theme",
                "reset_colors": "Reset to Default Colors",
                "reset_success": "Reset to default colors",
                "language": "Language",
                "select_language": "Select Language",
                "export_language": "Export Language File",
                "reset_message_title": "Information",
                "select_folder_title": "Select Folder",
                "export_dialog_title": "Export {0} Language File"
            },
            "analysis": {
                "mean": "Mean",
                "median": "Median",
                "std_dev": "Std Dev",
                "max": "Max",
                "min": "Min",
                "range": "Range"
            },
            "log": {
                "title": "Log",
                "error": "Error",
                "warning": "Warning",
                "info": "Info",
                "level": "Log Level:",
                "toggle": "Toggle",
                "clear": "Clear",
                "toggle_tooltip": "Toggle log filter level"
            }
        },
        "command_panel": {
            "title": "Settings",
            "select_port": "Select Port",
            "refresh": "Refresh",
            "connect": "Connect/Disconnect",
            "baudrate": "Baudrate",
            "auto_save": "Auto Save",
            "enable": "Enable",
            "dashboard": "Show Dashboard",
            "no_ports": "No available ports"
        },
        "color": {
            "background": "Background",
            "surface": "Surface",
            "text_primary": "Primary Text",
            "text_secondary": "Secondary Text",
            "accent": "Accent",
            "border_hover": "Border Hover",
            "select_color_title": "Select {0} Color"
        },
        "error": {
            "title": "Error",
            "error": "Error",
            "failed_to_load": "Failed to load data: ",
            "export_success": "Success",
            "export_failed": "Export language file failed",
            "export_message": "Language file exported to:",
            "json_filter": "JSON Files (*.json)"
        }
    }
    
    ensure_i18n_dir()
    
    # 保存中文翻译
    zh_file = os.path.join(I18N_DIR, "zh_CN.json")
    if not os.path.exists(zh_file):
        with open(zh_file, 'w', encoding='utf-8') as f:
            json.dump(zh_translations, f, ensure_ascii=False, indent=2)
    
    # 保存英文翻译
    en_file = os.path.join(I18N_DIR, "en_US.json")
    if not os.path.exists(en_file):
        with open(en_file, 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)


def export_language_file(language_code: str, export_path: str):
    """导出指定语言的翻译文件
    
    Args:
        language_code: 语言代码 (e.g., 'zh_CN', 'en_US')
        export_path: 导出文件路径
    
    Returns:
        bool: 导出是否成功
    """
    if language_code not in _supported_languages:
        return False
    
    language_file = os.path.join(I18N_DIR, f"{language_code}.json")
    
    if os.path.exists(language_file):
        try:
            shutil.copy2(language_file, export_path)
            return True
        except Exception as e:
            print(f"Error exporting language file: {e}")
            return False
    return False
