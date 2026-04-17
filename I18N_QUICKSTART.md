# SensorReceiver 多语言功能快速开始

## 🌍 新增功能

SensorReceiver 现已支持多语言界面！用户可以在设置中轻松切换语言。

## 🚀 快速开始

### 切换语言
1. 打开应用程序
2. 点击右侧的"设置"按钮
3. 在设置页面的"语言"选项中选择所需语言
4. 语言选择会自动保存
5. 重启应用以应用所有更改（某些动态元素可能需要）

### 支持的语言
- 🇨🇳 **简体中文** (中文)
- 🇬🇧 **English** (英文)

## 📋 支持的翻译范围

✅ 所有主要页面标题
✅ 所有按钮和菜单文本
✅ 设置项标签
✅ 错误消息和日志等级
✅ 工具提示

## 🔧 开发者信息

### 访问翻译
```python
from i18n import t

# 简单使用
text = t("page.homepage.title")  # 返回 "首页" 或 "Home"
```

### 翻译文件位置
- 翻译文件: `i18n/zh_CN.json` 和 `i18n/en_US.json`
- 语言偏好: `config/language.json`

### 添加新翻译
编辑翻译文件并在代码中使用 `t()` 函数。详见 `I18N_GUIDE.md`

## 📚 文档

- **I18N_GUIDE.md** - 完整的多语言系统使用指南
- **I18N_CHANGELOG.md** - 详细的更新日志
- **test_i18n.py** - i18n系统测试脚本

## 🧪 测试

运行测试脚本验证i18n功能：
```bash
python test_i18n.py
```

## ⚙️ 系统架构

```
SensorReceiver
├── i18n.py                 # i18n核心模块
├── i18n/
│   ├── zh_CN.json         # 中文翻译
│   └── en_US.json         # 英文翻译
├── config/
│   └── language.json      # 语言偏好配置
└── Pages.py               # 更新以支持i18n
```

## 🎯 核心特性

### 1. 自动语言检测
应用启动时会加载用户之前选择的语言（默认中文）

### 2. 即时更新
大部分UI文本切换语言时立即更新

### 3. 持久化存储
语言选择自动保存，应用下次启动时恢复

### 4. 可扩展性
易于添加新语言或新翻译

## 📝 翻译键命名规则

翻译键使用点号分隔的路径：
- `page.homepage.title` - 首页标题
- `command_panel.connect` - 连接按钮
- `error.failed_to_load` - 加载失败错误

## 💡 使用示例

### 在UI中使用翻译
```python
from PySide6.QtWidgets import QLabel, QPushButton
from i18n import t

# 创建标签
label = QLabel(t("page.homepage.title"))

# 创建按钮
button = QPushButton(t("page.settings.apply"))
```

### 在页面中实现语言切换
```python
def update_ui_text(self):
    """更新所有UI文本"""
    self.button.setText(t("page.settings.send_button"))
    self.label.setText(t("page.settings.save_directory"))
```

## 🌐 支持更多语言

要添加新语言（例如日文），请：
1. 在 `i18n/` 创建 `ja_JP.json`
2. 在 `i18n.py` 中的 `_supported_languages` 注册
3. 翻译所有文本

## 📊 项目统计

- 支持语言: 2
- 翻译键总数: 65+
- 覆盖率: 100% (中文/英文)

## 🐛 已知限制

- 某些由第三方库生成的文本（如样式名称）可能不支持翻译
- 某些组件可能需要应用重启才能应用新语言

## 🔗 相关文件

| 文件 | 描述 |
|------|------|
| i18n.py | i18n核心模块 |
| Pages.py | UI页面（已更新支持i18n） |
| MainWindow.py | 主窗口（已更新支持i18n） |
| I18N_GUIDE.md | 详细使用指南 |
| I18N_CHANGELOG.md | 更新日志 |
| test_i18n.py | 测试脚本 |

## ✨ 下一步

- 测试各种语言的UI布局
- 根据需要添加更多语言
- 完善文档和帮助文本的翻译

---

有问题？查看 `I18N_GUIDE.md` 了解更多信息。
