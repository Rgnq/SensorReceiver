# Nuitka 打包故障排查指南

## 🔍 快速诊断

运行此脚本以诊断常见问题：

```bash
python -c "
import os
import sys
from pathlib import Path

print('=== Nuitka 打包诊断 ===\n')

# 1. 检查 Nuitka 安装
print('[1] 检查 Nuitka 安装...')
try:
    import nuitka
    print(f'✓ Nuitka 已安装: {nuitka.__version__}')
except ImportError:
    print('✗ Nuitka 未安装: pip install nuitka')

# 2. 检查编译器
print('\n[2] 检查 C 编译器...')
import shutil
if sys.platform == 'win32':
    if shutil.which('cl'):
        print('✓ MSVC 编译器可用')
    elif shutil.which('gcc'):
        print('✓ GCC 编译器可用')
    else:
        print('✗ 未找到编译器')
else:
    if shutil.which('gcc') or shutil.which('clang'):
        print('✓ C 编译器可用')
    else:
        print('✗ 未找到编译器')

# 3. 检查项目结构
print('\n[3] 检查项目结构...')
required = ['main.py', 'i18n.py', 'i18n', 'Pages.py', 'MainWindow.py']
for item in required:
    path = Path(item)
    if path.exists():
        print(f'✓ {item} 存在')
    else:
        print(f'✗ {item} 缺失')

# 4. 检查 i18n 文件
print('\n[4] 检查 i18n 翻译文件...')
i18n_dir = Path('i18n')
if i18n_dir.exists():
    files = list(i18n_dir.glob('*.json'))
    print(f'✓ i18n 目录存在，包含 {len(files)} 个文件')
    for f in files:
        size = f.stat().st_size
        print(f'  - {f.name}: {size} 字节')
else:
    print('✗ i18n 目录不存在')

print('\n=== 诊断完成 ===')
"
```

## 📋 常见问题和解决方案

### 问题 1: Nuitka 未安装

**症状**
```
ModuleNotFoundError: No module named 'nuitka'
```

**解决方案**
```bash
# 安装 Nuitka
pip install nuitka

# 验证安装
python -m nuitka --version

# 安装可选依赖（提高性能）
pip install zstandard
```

---

### 问题 2: 找不到 C 编译器

**症状**
```
Error: No C compiler found!
```

**Windows 解决方案**
```bash
# 方案1: 安装 Visual Studio Build Tools
# 下载: https://visualstudio.microsoft.com/downloads/
# 选择 "Desktop development with C++"

# 方案2: 安装 MinGW
choco install mingw  # 如果有 Chocolatey

# 方案3: 使用 Visual Studio Community
# 下载并安装完整的 Visual Studio Community
```

**Linux 解决方案**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# RedHat/CentOS
sudo yum install gcc python3-devel

# macOS
xcode-select --install
```

---

### 问题 3: 翻译文件未被包含

**症状**
- UI 显示翻译键而不是文本（"page.settings.language"）
- 设置页面无法加载语言选项

**原因检查**
```bash
# 1. 检查 i18n 目录是否存在
dir i18n

# 2. 检查打包脚本是否包含了 --include-data-dir
type nuitka_build.py | find "include-data-dir"

# 3. 检查打包输出中是否包含 i18n
dir dist\SensorReceiver\i18n
```

**解决方案**
```bash
# 使用正确的打包脚本
python nuitka_build.py

# 或手动指定路径
python -m nuitka ^
    --follow-imports ^
    --include-data-dir=i18n=i18n ^
    --include-data-dir=config=config ^
    --standalone ^
    main.py
```

---

### 问题 4: 打包后程序无法启动

**症状**
```
Error: Cannot find module 'PySide6'
或其他导入错误
```

**诊断步骤**
```bash
# 1. 在开发环境测试
python main.py  # 应该能运行

# 2. 检查 Python 路径
python -m site

# 3. 列出所有已安装的包
pip list | findstr PySide6

# 4. 重新安装依赖
pip install -r requirements.txt
```

**解决方案**
```bash
# 确保所有依赖都已安装
pip install PySide6 pyserial qt-material

# 重新打包
python nuitka_build.py
```

---

### 问题 5: 打包文件过大

**症状**
```
打包后的文件 > 500MB
```

**原因分析**
```bash
# 查看输出目录大小
dir /S dist

# 查看主要占用
du -sh dist\SensorReceiver\*
```

**解决方案**
```python
# 方案1: 使用单文件版本（自动压缩）
python nuitka_build.py --onefile

# 方案2: 删除不必要的文件
# 检查 dist\SensorReceiver\ 中是否有：
# - 不需要的 DLL
# - 测试文件
# - 文档文件

# 方案3: 优化打包选项
python -m nuitka \
    --onefile \
    --no-include-qt-plugins=imageformats \
    main.py
```

---

### 问题 6: 配置文件无法保存

**症状**
- 语言选择无法保存
- 主题颜色改变后无效
- 重启程序后设置恢复到默认值

**原因检查**
```python
# 在 Pages.py 中添加以下代码来调试
import os
from i18n import LANGUAGE_CONFIG

config_dir = os.path.dirname(LANGUAGE_CONFIG)
print(f"配置目录: {config_dir}")
print(f"是否存在: {os.path.exists(config_dir)}")
print(f"是否可写: {os.access(config_dir, os.W_OK)}")
```

**解决方案**
```bash
# 1. 检查权限
# 确保应用有权写入安装目录

# 2. 使用用户目录
# 修改 i18n.py 使用用户 AppData 目录

# 3. 以管理员身份运行
# 右键 > 以管理员身份运行
```

---

### 问题 7: 首次启动很慢（单文件版本）

**症状**
```
首次启动需要 30-60 秒
后续启动正常（5-10 秒）
```

**原因**
- 单文件版本需要解压到临时目录
- Python 需要初始化

**解决方案**
```bash
# 1. 使用独立版本代替
python nuitka_build.py --standalone

# 2. 在 UI 中显示加载进度
# 添加启动画面或进度条

# 3. 告知用户首次启动较慢
# 在使用说明中说明这一点
```

---

### 问题 8: 语言切换后 UI 未更新

**症状**
- 某些文本没有改变
- 部分按钮仍显示旧语言

**原因检查**
```python
# 检查是否所有页面都实现了 update_ui_text()
# 在 MainWindow.py 中
def update_ui_text(self):
    # 应该包含对所有页面的调用
    self.Homepage.update_ui_text()
    self.HistoryPage.update_ui_text()
    self.SettingsPage.update_ui_text()
    self.LogPage.update_ui_text()
```

**解决方案**
```python
# 1. 添加调试输出
print("更新UI文本中...")

# 2. 检查页面是否实现了 update_ui_text()
# 搜索: "def update_ui_text"

# 3. 重新启动应用
# 某些 Qt 组件可能需要重启才能完全更新

# 4. 强制刷新
self.repaint()
self.update()
```

---

### 问题 9: 打包后打不开数据文件

**症状**
- 无法读取历史数据
- 无法保存主题配置
- 文件对话框选择的路径无效

**解决方案**
```python
# 检查路径是否使用了相对路径
# 应该使用 os.path 处理路径

# 不要硬编码路径
# ❌ 错误
config_path = "config/language.json"

# ✅ 正确
from i18n import LANGUAGE_CONFIG
```

---

### 问题 10: 程序闪退

**症状**
```
程序启动后立即关闭
无任何错误信息
```

**诊断方法**
```bash
# 1. 从命令行运行以查看错误
cd dist\SensorReceiver
main.exe

# 2. 创建启动脚本
echo off
main.exe
pause

# 3. 查看 Windows 事件查看器
# Windows + R > eventvwr.msc
```

**常见原因和解决方案**
```python
# 原因1: main() 函数未被正确调用
# 检查 main.py 底部
if __name__ == "__main__":
    main()  # 必须有这一行

# 原因2: 模块导入失败
# 添加调试输出
try:
    from Pages import Homepage
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

# 原因3: Qt 插件缺失
# 确保 Nuitka 包含了 Qt 插件
python -m nuitka \
    --follow-imports \
    --include-qt-plugins \
    main.py
```

---

## 🧪 完整测试清单

运行以下测试以确保打包成功：

```bash
# 1. 启动程序
.\dist\SensorReceiver\main.exe

# 2. 检查 UI
# - [ ] 所有文本显示为中文
# - [ ] 窗口标题正确
# - [ ] 图标正确显示

# 3. 功能测试
# - [ ] 点击设置打开设置面板
# - [ ] 设置页面显示语言选项
# - [ ] 可以选择 English

# 4. 语言切换
# - [ ] 选择 English 后 UI 立即改变
# - [ ] 所有文本都翻译为英文
# - [ ] 关闭并重启，英文仍被选中

# 5. 数据功能
# - [ ] 串口连接正常
# - [ ] 可以接收数据
# - [ ] 图表显示正常

# 6. 配置保存
# - [ ] config/language.json 被创建
# - [ ] 改变主题色后保存成功
# - [ ] 重启程序设置被记住
```

---

## 📊 打包验证脚本

创建 `verify_package.py`：

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""验证打包结果"""

import os
import json
from pathlib import Path

def verify_package():
    """验证打包的完整性"""
    print("=== 打包验证 ===\n")
    
    checks = {
        "可执行文件": "dist\\SensorReceiver\\main.exe",
        "i18n 中文": "dist\\SensorReceiver\\i18n\\zh_CN.json",
        "i18n 英文": "dist\\SensorReceiver\\i18n\\en_US.json",
        "config 目录": "dist\\SensorReceiver\\config",
    }
    
    for name, path in checks.items():
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"{status} {name}: {path}")
        
        # 如果是 JSON 文件，检查有效性
        if path.endswith('.json') and exists:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    keys = len(data.get('page', {}).get('homepage', {}))
                    print(f"   └─ 包含 {keys} 个翻译键")
            except Exception as e:
                print(f"   └─ 错误: {e}")
    
    print("\n验证完成")

if __name__ == "__main__":
    verify_package()
```

运行验证：
```bash
python verify_package.py
```

---

## 💡 高级调试技巧

### 1. 启用详细日志

```bash
# Nuitka 详细输出
python -m nuitka \
    --verbose \
    --include-data-dir=i18n=i18n \
    --standalone \
    main.py
```

### 2. 保留中间文件

```bash
# 保留编译产物便于调试
python -m nuitka \
    --keep-build-dir \
    --standalone \
    main.py
```

### 3. 生成依赖图

```bash
# 查看模块依赖关系
python -m nuitka \
    --show-modules \
    main.py > dependencies.txt
```

---

## 📞 获取帮助

如果以上方案都无法解决：

1. **查看 Nuitka 文档**
   - https://nuitka.net/

2. **检查项目文档**
   - `NUITKA_PACKAGING_GUIDE.md`
   - `I18N_NUITKA_INTEGRATION.md`

3. **创建最小化测试案例**
   ```bash
   # 创建简单的测试程序
   # 逐步添加功能
   # 找出导致问题的具体部分
   ```

4. **查看错误日志**
   ```bash
   # Nuitka 可能生成的日志文件
   type build\*.log
   type *.log
   ```

---

**文档版本**: 1.0  
**更新日期**: 2026年4月17日  
**适用于**: Nuitka 1.7+
