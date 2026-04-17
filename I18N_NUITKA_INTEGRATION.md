# i18n 在 Nuitka 打包中的集成指南

## 🎯 概述

本文档详细说明如何在 Nuitka 打包应用程序中正确处理 i18n 翻译文件的加载。

## 🔧 核心机制

### 1. 路径自动检测

i18n.py 在初始化时会自动检测运行环境：

```python
def _get_base_path():
    """检测基础路径"""
    # 情况1: PyInstaller 打包
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    
    # 情况2: Nuitka 打包 ← 我们关注的
    elif getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    
    # 情况3: 开发模式
    else:
        return os.path.dirname(os.path.abspath(__file__))
```

### 2. 资源目录结构

```
打包后的应用/
├── main.exe                    # Nuitka 生成的可执行文件
│
├── i18n/                       # --include-data-dir=i18n=i18n
│   ├── zh_CN.json             # 自动放置在此
│   └── en_US.json
│
└── config/                     # --include-data-dir=config=config
    ├── language.json          # 用户语言偏好
    └── dark_theme_colors.json # 主题配置
```

## 📋 打包配置详解

### Nuitka 打包命令

```bash
python -m nuitka ^
    --follow-imports ^
    --include-data-dir=i18n=i18n ^
    --include-data-dir=config=config ^
    --output-dir=build\nuitka ^
    --standalone ^
    main.py
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--follow-imports` | 跟踪所有导入，包括 i18n 模块 |
| `--include-data-dir=i18n=i18n` | 复制 i18n 目录到输出中 |
| `--include-data-dir=config=config` | 复制 config 目录到输出中 |
| `--output-dir=BUILD_DIR` | 输出目录 |
| `--standalone` | 包含所有依赖 |

## 🔄 加载流程

### 开发模式 vs 打包模式

```
┌─────────────────────────────────────┐
│  应用启动                           │
└─────────┬───────────────────────────┘
          │
          ▼
    ┌─────────────────┐
    │ 检测运行环境     │
    └─────────┬───────┘
              │
      ┌───────┴───────┐
      │               │
      ▼               ▼
  开发模式        Nuitka打包
      │               │
      ▼               ▼
  当前目录    EXE所在目录
      │               │
      ▼               ▼
  i18n/          i18n/
```

### 代码路径追踪

```python
# 1. 应用启动：main.py
initialize_i18n()

# 2. i18n.py 检测环境
_BASE_PATH = _get_base_path()
# 开发: "/path/to/SensorReceiver"
# 打包: "C:\\Program Files\\SensorReceiver"

# 3. 构造路径
I18N_DIR = os.path.join(_BASE_PATH, "i18n")
# 开发: "/path/to/SensorReceiver/i18n"
# 打包: "C:\\Program Files\\SensorReceiver\\i18n"

# 4. 加载翻译
load_language('zh_CN')
# 从 I18N_DIR/zh_CN.json 读取
```

## 💾 文件保存位置

### 语言偏好保存

```python
LANGUAGE_CONFIG = os.path.join(_BASE_PATH, "config", "language.json")

# 开发模式:
# ./config/language.json

# 打包模式:
# C:\Program Files\SensorReceiver\config\language.json
```

### 文件内容示例

```json
{
  "language": "zh_CN"
}
```

## 🎛️ 应用于 MainWindow 和 Pages

### 初始化流程

```python
# main.py
from i18n import initialize_i18n

def main():
    initialize_i18n()  # 1. 初始化i18n系统
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()
```

### UI 使用翻译

```python
# Pages.py
from i18n import t

class SettingsPage(QWidget):
    def initUI(self):
        # 使用翻译的文本
        language_label = QLabel(t("page.settings.language"))
        # 在打包环境中自动从正确的路径加载
```

## 🏗️ 分步配置指南

### 步骤1: 验证项目结构

```
SensorReceiver/
├── main.py                    ← 打包的入口点
├── i18n.py                    ← i18n 模块
├── Pages.py
├── MainWindow.py
│
├── i18n/                      ← 必须存在
│   ├── zh_CN.json
│   └── en_US.json
│
└── config/                    ← 必须存在
    └── (会在运行时创建)
```

### 步骤2: 准备打包脚本

使用提供的 `nuitka_build.py`：

```bash
python nuitka_build.py
```

### 步骤3: 验证打包结果

```bash
# 检查输出结构
dir /S dist\SensorReceiver\

# 应该包含：
# dist\SensorReceiver\main.exe
# dist\SensorReceiver\i18n\zh_CN.json
# dist\SensorReceiver\i18n\en_US.json
```

### 步骤4: 测试打包版本

```bash
# 运行打包后的程序
.\dist\SensorReceiver\main.exe

# 验证：
# 1. UI 显示中文
# 2. 设置页面能选择语言
# 3. 切换语言有效
# 4. 关闭并重启，检查语言是否被记住
```

## 🔍 调试技巧

### 1. 检查 i18n 是否正确初始化

```python
from i18n import _BASE_PATH, I18N_DIR, get_current_language

print(f"BASE_PATH: {_BASE_PATH}")
print(f"I18N_DIR: {I18N_DIR}")
print(f"CURRENT_LANG: {get_current_language()}")
print(f"I18N_DIR exists: {os.path.exists(I18N_DIR)}")
```

### 2. 检查翻译文件是否存在

```python
import os
from i18n import I18N_DIR

zh_file = os.path.join(I18N_DIR, "zh_CN.json")
en_file = os.path.join(I18N_DIR, "en_US.json")

print(f"zh_CN.json 存在: {os.path.exists(zh_file)}")
print(f"en_US.json 存在: {os.path.exists(en_file)}")
```

### 3. 在程序中输出调试信息

```python
# Pages.py 中添加
def initUI(self):
    print(f"使用的i18n目录: {I18N_DIR}")
    print(f"当前语言: {get_current_language()}")
    print(f"测试翻译: {t('page.settings.language')}")
```

### 4. 创建日志文件

```python
# 在 main.py 中添加
import logging

logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 在 i18n.py 中添加
logging.debug(f"i18n基础路径: {_BASE_PATH}")
logging.debug(f"加载语言: {language_code}")
```

## 📊 常见问题对照表

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 翻译文件未找到 | i18n 目录未被包含 | 添加 `--include-data-dir=i18n=i18n` |
| UI 显示翻译键 | 翻译文件路径错误 | 检查 `_BASE_PATH` 和 `I18N_DIR` |
| 语言改变无效 | 翻译文件加载失败 | 检查 JSON 文件格式 |
| 配置无法保存 | config 目录无写权限 | 添加 `--include-data-dir=config=config` |
| 打包文件太大 | 包含了不必要的依赖 | 使用 `--follow-imports` |

## ✅ 打包验证清单

- [ ] i18n 目录存在并包含 JSON 文件
- [ ] Nuitka 打包命令包含 `--include-data-dir=i18n=i18n`
- [ ] config 目录也被包含
- [ ] 打包后的目录结构正确
- [ ] 程序能正常启动
- [ ] 设置页面显示语言选项
- [ ] 语言切换生效
- [ ] 语言偏好被正确保存
- [ ] 关闭并重启程序，语言偏好被恢复
- [ ] 所有翻译文本显示正确

## 🔐 权限和路径问题

### Windows 权限问题

```python
# 如果 config 目录无法创建，可以使用用户目录
import os
from pathlib import Path

if os.name == 'nt':  # Windows
    # 使用 AppData 目录
    config_dir = Path.home() / "AppData" / "Local" / "SensorReceiver"
else:  # Linux/Mac
    config_dir = Path.home() / ".config" / "sensorreceiver"
```

### 便携式版本（U盘运行）

```python
# i18n.py 可以修改为优先使用相对路径
def _get_base_path():
    # 优先使用相对路径（便携式）
    if os.path.exists("i18n"):
        return os.path.dirname(os.path.abspath(__file__))
    # 否则使用 EXE 所在目录
    elif getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))
```

## 📈 性能考虑

### i18n 初始化性能

```python
# 初始化时间通常 < 100ms
initialize_i18n()  # 快速完成

# 后续翻译查询也很快
t("page.homepage.title")  # O(log n) 查询时间
```

### 打包后性能

- **启动时间**: +0-500ms（取决于翻译文件大小）
- **内存占用**: +5-10MB（翻译数据）
- **磁盘占用**: +1-2MB（翻译文件）

## 🎓 最佳实践

### 1. 总是使用 `t()` 函数

```python
# ✅ 正确
label.setText(t("page.settings.language"))

# ❌ 不正确（硬编码字符串）
label.setText("语言")
```

### 2. 在 `initUI()` 中使用翻译

```python
# ✅ 在初始化时使用
def initUI(self):
    self.button = QPushButton(t("page.settings.apply"))

# ⚠️ 在 update_ui_text() 中更新
def update_ui_text(self):
    self.button.setText(t("page.settings.apply"))
```

### 3. 在打包前测试

```bash
# 在开发环境中完整测试
python main.py

# 检查是否所有文本都正确翻译
# 测试语言切换功能
# 验证配置保存功能
```

### 4. 包含错误处理

```python
# 在 i18n.py 中添加
try:
    _translations = json.load(f)
except json.JSONDecodeError:
    print(f"错误: 无法解析 {language_file}")
    # 回退到默认语言
```

## 📞 故障排查流程

1. **确认 i18n 目录存在**
   ```bash
   ls i18n/  # Linux/Mac
   dir i18n  # Windows
   ```

2. **运行打包脚本**
   ```bash
   python nuitka_build.py
   ```

3. **检查打包输出**
   ```bash
   dir dist\SensorReceiver\i18n
   ```

4. **测试打包程序**
   ```bash
   .\dist\SensorReceiver\main.exe
   ```

5. **查看日志**
   ```bash
   type debug.log  # Windows
   cat debug.log   # Linux/Mac
   ```

---

**文档版本**: 1.0  
**Nuitka 版本**: 1.7+  
**Python 版本**: 3.8+  
**更新日期**: 2026年4月17日
