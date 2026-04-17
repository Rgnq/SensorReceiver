# Nuitka 打包快速参考

## 🚀 一键打包

```bash
# 最简单的方式 - 推荐用于首次打包
python nuitka_build.py

# 单文件版本（便携式）
python nuitka_build.py --onefile

# 不复制到 dist 目录（仅保留在 build 目录）
python nuitka_build.py --no-copy
```

## 📋 打包前检查清单

```bash
# 1. 检查项目结构
[ ] main.py 存在
[ ] i18n.py 存在
[ ] i18n/ 目录存在（包含 JSON 文件）
[ ] Pages.py, MainWindow.py 等存在

# 2. 检查环境
[ ] Python 3.8+ 已安装
[ ] nuitka 已安装 (pip install nuitka)
[ ] C 编译器已安装
    - Windows: MSVC 或 MinGW
    - Linux: gcc 或 clang
    - macOS: Xcode

# 3. 测试开发版本
[ ] python main.py 能正常运行
[ ] UI 显示中文
[ ] 语言选择功能正常
[ ] 串口连接正常
```

## 🎯 核心命令

### 基础打包
```bash
python -m nuitka \
    --follow-imports \
    --include-data-dir=i18n=i18n \
    --include-data-dir=config=config \
    --standalone \
    main.py
```

### 单文件打包
```bash
python -m nuitka \
    --follow-imports \
    --include-data-dir=i18n=i18n \
    --include-data-dir=config=config \
    --standalone \
    --onefile \
    main.py
```

### 优化打包（更小的文件）
```bash
python -m nuitka \
    --follow-imports \
    --include-data-dir=i18n=i18n \
    --include-data-dir=config=config \
    --output-dir=build\nuitka \
    --standalone \
    --onefile \
    -O \
    main.py
```

## 📦 打包后的文件结构

### 独立版本
```
dist/
└── SensorReceiver/
    ├── main.exe
    ├── i18n/
    │   ├── zh_CN.json
    │   └── en_US.json
    ├── config/
    │   └── (用户配置)
    └── library.zip
```

### 单文件版本
```
dist/
└── SensorReceiver.exe
```

## 🧪 打包后测试

```bash
# 1. 运行程序
.\dist\SensorReceiver\main.exe

# 2. 检查列表
[_] UI 显示正确
[_] 能选择语言
[_] 语言切换生效
[_] 关闭重启后语言被记住
[_] 所有功能正常
[_] config/language.json 被创建
```

## 🔧 常见参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--standalone` | 包含所有依赖 | 必需 |
| `--onefile` | 打包为单个文件 | 可选 |
| `--follow-imports` | 跟踪导入 | 推荐 |
| `--include-data-dir` | 包含数据目录 | `--include-data-dir=i18n=i18n` |
| `--output-dir` | 输出目录 | `--output-dir=build` |
| `-O` | 优化 | 可选 |
| `--remove-output` | 移除旧输出 | 可选 |

## 📊 快速性能对比

| 方案 | 构建时间 | 文件大小 | 启动时间 | 适用场景 |
|------|--------|--------|--------|--------|
| 独立版 | 5-10分钟 | 200-300MB | 3-5秒 | 生产环境 |
| 单文件版 | 10-15分钟 | 200-300MB | 首次30秒 | U盘版本 |

## 🐛 快速故障排查

### 问题: 翻译文件未找到
```bash
# 解决: 检查打包命令中是否包含
--include-data-dir=i18n=i18n
```

### 问题: UI 显示翻译键
```bash
# 解决: 检查 i18n 目录是否在输出中
dir dist\SensorReceiver\i18n
```

### 问题: 无法保存配置
```bash
# 解决: 检查 config 目录是否被包含
--include-data-dir=config=config
```

### 问题: 找不到编译器
```bash
# Windows 解决:
# 1. 安装 Visual Studio Build Tools
# 2. 或安装 MinGW
# 3. 重启 IDE/终端
```

### 问题: 打包失败
```bash
# 解决步骤:
# 1. python main.py 能运行吗? 是 -> 继续
# 2. python -m nuitka --version 能运行吗? 是 -> 继续
# 3. 检查编译器是否安装
# 4. 增加打包命令中的 --verbose 查看详细输出
```

## 📝 脚本使用

### nuitka_build.py 选项

```bash
# 默认 (独立版本，复制到 dist)
python nuitka_build.py

# 仅构建，不复制
python nuitka_build.py --no-copy

# 单文件版本
python nuitka_build.py --onefile

# 单文件版本，不复制
python nuitka_build.py --onefile --no-copy
```

## ✅ 验证清单

```bash
# 步骤1: 准备
[ ] 所有依赖已安装
[ ] 项目在开发环境能正常运行

# 步骤2: 打包
[ ] python nuitka_build.py 无错误
[ ] dist 目录已生成

# 步骤3: 验证
[ ] dist\SensorReceiver\main.exe 存在
[ ] i18n 目录已包含
[ ] config 目录已包含

# 步骤4: 测试
[ ] 程序能启动
[ ] UI 显示正确
[ ] 所有功能正常
[ ] 配置能保存
```

## 🎓 关键文件

| 文件 | 用途 |
|------|------|
| `nuitka_build.py` | 打包脚本 |
| `i18n.py` | i18n 模块（支持打包） |
| `i18n/zh_CN.json` | 中文翻译 |
| `i18n/en_US.json` | 英文翻译 |
| `NUITKA_PACKAGING_GUIDE.md` | 详细指南 |
| `I18N_NUITKA_INTEGRATION.md` | i18n 集成 |
| `NUITKA_TROUBLESHOOTING.md` | 故障排查 |

## 🔗 相关命令

```bash
# 检查 Nuitka 版本
python -m nuitka --version

# 显示所有选项
python -m nuitka --help

# 设置编译器 (Windows)
python -m nuitka --clang main.py  # 使用 Clang
python -m nuitka --gcc main.py    # 使用 GCC
```

## 📞 快速链接

- **Nuitka 官网**: https://nuitka.net/
- **Nuitka 文档**: https://nuitka.net/doc/
- **本项目 i18n 指南**: `I18N_GUIDE.md`
- **打包详细指南**: `NUITKA_PACKAGING_GUIDE.md`

---

**版本**: 1.0  
**日期**: 2026年4月17日  
**Nuitka**: 1.7+  
**Python**: 3.8+

💡 **提示**: 标记为"推荐"的选项是最安全、最常用的选择。
