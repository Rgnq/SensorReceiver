# SensorReceiver Nuitka 打包指南

## 📦 概述

本指南说明如何使用 Nuitka 将 SensorReceiver 应用程序打包为可执行文件，并将翻译文件（i18n）内置到可执行文件中。

## 🎯 支持的打包方式

### 方案1: 独立版本（推荐）
- **优点**: 包含所有依赖，无需安装Python
- **缺点**: 文件较大 (~200-300MB)
- **用途**: 生产环境、客户端分发

### 方案2: 单文件版本
- **优点**: 只有一个EXE文件
- **缺点**: 启动时需要解压，首次启动较慢
- **用途**: 便携式版本、U盘运行

### 方案3: 目录版本
- **优点**: 启动快速，文件分离便于调试
- **缺点**: 多个文件，体积大
- **用途**: 本地开发和测试

## 📋 前提条件

### 1. 安装依赖

```bash
# 安装 Nuitka 和编译器
pip install nuitka
pip install zstandard  # 压缩支持（可选）

# Windows 需要 Visual Studio Build Tools 或 MinGW
# 推荐：安装 Visual C++ 构建工具
```

### 2. 验证环境

```bash
# 验证 Nuitka 安装
python -m nuitka --version

# 验证 C 编译器
# Windows: 检查 MSVC 或 gcc 是否可用
where cl    # MSVC
where gcc   # MinGW
```

## 🚀 快速开始

### 方式1: 使用打包脚本（推荐）

```bash
# 构建独立版本（推荐）
python nuitka_build.py

# 构建单文件版本
python nuitka_build.py --onefile

# 不复制到 dist 目录
python nuitka_build.py --no-copy
```

### 方式2: 手动命令

#### 独立版本
```bash
python -m nuitka ^
    --follow-imports ^
    --include-data-dir=i18n=i18n ^
    --include-data-dir=config=config ^
    --output-dir=build\nuitka ^
    --standalone ^
    main.py
```

#### 单文件版本
```bash
python -m nuitka ^
    --follow-imports ^
    --include-data-dir=i18n=i18n ^
    --include-data-dir=config=config ^
    --output-dir=build\nuitka ^
    --standalone ^
    --onefile ^
    main.py
```

## 📁 打包后的目录结构

### 独立版本
```
dist/
└── SensorReceiver/
    ├── main.exe              # 主程序
    ├── i18n/                 # 翻译文件（内置）
    │   ├── zh_CN.json
    │   └── en_US.json
    ├── config/               # 配置文件（内置）
    │   └── language.json
    └── library.zip           # 标准库和依赖
```

### 单文件版本
```
dist/
└── SensorReceiver.exe        # 包含所有内容的单个EXE
```

## 🔧 关键配置说明

### 1. 翻译文件包含

```bash
--include-data-dir=i18n=i18n
```

**说明**：
- 第一个 `i18n` = 源目录（相对于构建脚本位置）
- 第二个 `i18n` = 目标目录（相对于可执行文件）

### 2. 配置文件包含

```bash
--include-data-dir=config=config
```

**说明**：
- 包含 `config` 目录，包括颜色主题和语言偏好

### 3. 其他常用选项

```bash
--follow-imports              # 跟踪所有导入
--standalone                  # 包含所有依赖
--onefile                     # 打包为单个文件
-O                            # 优化编译
--remove-output               # 移除旧输出
--output-dir=BUILD_DIR        # 输出目录
```

## 🔍 i18n 在打包中如何工作

### 开发模式（运行脚本）
```
当前目录/
├── main.py
├── i18n/
│   ├── zh_CN.json
│   └── en_US.json
└── config/
    └── language.json
```

**加载方式**: 从脚本所在目录加载

### Nuitka 打包模式（运行EXE）
```
可执行文件所在目录/
├── main.exe
├── i18n/          ← Nuitka 自动放置
│   ├── zh_CN.json
│   └── en_US.json
└── config/        ← Nuitka 自动放置
    └── language.json
```

**加载方式**: i18n.py 自动检测并从 EXE 所在目录加载

## 🔑 i18n 自动检测机制

```python
# i18n.py 中的路径检测逻辑
def _get_base_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # PyInstaller 模式
        return sys._MEIPASS
    elif getattr(sys, 'frozen', False):
        # Nuitka 模式 ← 这里
        return os.path.dirname(sys.executable)
    else:
        # 开发模式
        return os.path.dirname(os.path.abspath(__file__))
```

## 📊 性能对比

| 方案 | 文件大小 | 启动速度 | 适用场景 |
|------|--------|--------|--------|
| 独立版 | 200-300MB | 中等 | 生产环境 |
| 单文件版 | 200-300MB | 慢（首次） | 便携式 |
| 目录版 | 200-300MB | 快 | 开发测试 |

## 🧪 测试打包结果

### 1. 检查翻译是否正常加载

```bash
# 运行打包后的程序
.\dist\SensorReceiver\main.exe

# 验证：
# 1. 设置页面能否看到语言选择
# 2. 切换语言时UI文本是否改变
# 3. 打开应用两次，检查语言选择是否被保存
```

### 2. 检查配置文件是否正常保存

```bash
# 检查输出目录中是否生成了新文件
dir dist\SensorReceiver\config\

# 应该包含：
# - language.json（用户选择的语言）
# - dark_theme_colors.json（主题颜色）
```

### 3. 完整测试清单

- ✅ 程序启动时加载中文界面
- ✅ 在设置中能够选择语言
- ✅ 选择英文后UI文本全部改变
- ✅ 关闭程序并重启，检查语言是否被记住
- ✅ 检查 `config/language.json` 文件是否已创建
- ✅ 验证所有串口功能正常工作
- ✅ 测试图表和数据显示功能

## 🐛 常见问题

### Q1: 打包后无法找到翻译文件
**症状**: 界面显示翻译键而不是文本
**原因**: 翻译文件未被正确包含
**解决方案**:
```bash
# 检查 i18n 目录是否存在
# 确保使用了 --include-data-dir=i18n=i18n
# 验证路径是相对于构建脚本位置的
```

### Q2: 程序启动后创建的文件位置不对
**症状**: 无法保存语言选择或配置
**原因**: 权限问题或目录不存在
**解决方案**:
```python
# i18n.py 会自动创建 config 目录
# 确保应用有写入权限
# 检查 LANGUAGE_CONFIG 的路径是否正确
```

### Q3: 打包文件太大（>300MB）
**原因**: 包含了过多的依赖库
**优化方案**:
```bash
# 使用压缩
pip install zstandard

# 添加以下参数
--follows-imports=pyside6
--include-package=PySide6
--include-data-file=...
```

### Q4: 首次启动单文件版本很慢
**原因**: 需要解压文件到临时目录
**解决方案**:
- 使用独立版本代替
- 或告知用户首次启动较慢

## 📝 打包脚本使用指南

### nuitka_build.py 功能

```bash
# 基础用法
python nuitka_build.py

# 可用选项
--standalone    # 默认为独立版本
--onefile       # 打包为单个文件
--no-copy       # 不复制到 dist 目录
```

### 脚本工作流程

1. **检查资源** → 验证 i18n 和 config 目录存在
2. **构建** → 使用 Nuitka 编译
3. **复制** → 复制到 dist 目录（可选）
4. **验证** → 检查输出文件

## 🔐 分发注意事项

### 1. 运行时权限
- 应用需要创建 `config/language.json`
- 确保用户有写入权限

### 2. 依赖项
- 不需要 Python 运行环境
- 不需要安装任何库
- 完全独立

### 3. 版本标识
```bash
# 添加版本信息（可选）
--company-name="YourCompany"
--product-name="SensorReceiver"
--product-version="2.0.0"
```

## 📦 发布清单

- ✅ 使用 nuitka_build.py 生成可执行文件
- ✅ 测试所有功能正常工作
- ✅ 验证翻译文件被正确加载
- ✅ 创建 `README.txt`（使用说明）
- ✅ 创建 `CHANGELOG.txt`（更新日志）
- ✅ 压缩为 ZIP 或 MSI
- ✅ 上传到发布服务器

## 🎓 相关文件

| 文件 | 说明 |
|------|------|
| nuitka_build.py | Nuitka 打包脚本 |
| i18n.py | i18n 模块（已支持打包） |
| main.py | 主程序入口 |
| i18n/zh_CN.json | 中文翻译 |
| i18n/en_US.json | 英文翻译 |

## 💡 高级用法

### 创建 MSI 安装程序

```bash
# 使用 nuitka 输出 + WiX 工具链
# 或使用 PyInstaller 的替代品

# 生成独立版本后
python nuitka_build.py --standalone
```

### 自动更新支持

```python
# 可在应用中添加检查更新功能
# 更新内容包括：
# - 主程序
# - i18n 翻译文件
# - 配置文件
```

### 多版本支持

```bash
# 32 位版本
python -m nuitka --arch=x86 main.py

# 64 位版本（默认）
python -m nuitka --arch=x64 main.py
```

## 📞 故障排除

如遇到问题，请按以下步骤排查：

1. **检查 Nuitka 安装**
   ```bash
   python -m nuitka --version
   ```

2. **验证编译器**
   ```bash
   # Windows
   python -c "import distutils.ccompiler; print(distutils.ccompiler.new_compiler().compiler_type)"
   ```

3. **测试打包脚本**
   ```bash
   python nuitka_build.py
   # 查看详细的构建日志
   ```

4. **检查输出文件**
   ```bash
   # 验证 i18n 目录是否在输出中
   dir /S dist
   ```

---

**最后更新**: 2026年4月17日  
**Nuitka 版本**: 最新稳定版  
**Python 版本**: 3.8+
