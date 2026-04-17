# SettingsPage 颜色调色盘快速参考

## 核心功能

### 用户功能
1. **自定义颜色** - 点击色块打开调色盘，选择新颜色
2. **切换主题** - 在"编辑主题"下拉框选择深色或浅色
3. **实时预览** - 修改后立即应用到整个应用
4. **一键重置** - 恢复所有颜色到默认值
5. **查看颜色值** - HEX颜色码自动显示

### 可自定义的6种颜色
| 颜色名称 | 用途 | 默认值(深) | 默认值(浅) |
|---------|------|----------|---------|
| Background | 窗口背景 | #121212 | #FFFFFF |
| Surface | 组件背景 | #1E1E1E | #C8C8C8 |
| Text_Primary | 主文本 | #E0E0E0 | #000000 |
| Text_Secondary | 副文本 | #A0A0A0 | #606060 |
| Accent | 强调色 | #BB86FC | #6200EE |
| Border_Hover | 边框悬停 | #333333 | #CCCCCC |

## 技术实现

### 关键代码路径

**保存颜色：**
```python
from colorstyle import save_theme_colors
save_theme_colors(True, {"Background": "#1A1A1A", ...})
```

**加载颜色：**
```python
from colorstyle import load_theme_colors
load_theme_colors()  # 自动从JSON加载
```

**重置颜色：**
```python
from colorstyle import reset_theme_colors
reset_theme_colors(True)  # 重置深色主题
```

### 配置文件位置
```
项目根目录/
└── config/
    ├── dark_theme_colors.json    # 深色主题配置
    └── light_theme_colors.json   # 浅色主题配置
```

### 文件变更清单
- `colorstyle.py` - +75行，添加颜色管理函数
- `Pages.py` - +150行，SettingsPage增强
- `MainWindow.py` - +5行，添加信号连接
- `COLOR_PICKER_GUIDE.md` - 完整文档

## UI流程

```
SettingsPage
    ↓
编辑主题选择框 [深色/浅色]
    ↓
颜色编辑面板 (6个颜色按钮)
    ↓
用户点击颜色按钮
    ↓
QColorDialog打开
    ↓
用户选择颜色
    ↓
颜色自动保存到JSON
    ↓
发出themeColorsChangedSignal信号
    ↓
MainWindow.on_theme_colors_changed()
    ↓
所有组件调用update_style()
    ↓
整个应用视觉更新
```

## 集成检查清单

✅ colorstyle.py
  - save_theme_colors() 实现
  - load_theme_colors() 实现
  - reset_theme_colors() 实现
  - 配置文件管理

✅ Pages.py
  - QColorDialog导入
  - SettingsPage重构
  - create_color_panel() 方法
  - on_color_button_clicked() 处理
  - themeColorsChangedSignal 信号

✅ MainWindow.py
  - 信号连接
  - on_theme_colors_changed() 处理

✅ 配置持久化
  - config目录创建
  - JSON文件格式
  - 读写功能

## 测试验证

✅ 颜色保存/加载
✅ 颜色重置
✅ JSON文件创建
✅ 信号发送
✅ UI更新
✅ 6种颜色编辑

## 使用示例

### Python代码调用
```python
# 导入
from colorstyle import *

# 加载用户自定义颜色
load_theme_colors()

# 在样式中使用
bg_color = dark_theme_colors['Background']

# 生成样式表
style = get_menubar_stylesheet(is_dark=True)
```

### 配置文件格式
```json
{
    "Background": "#121212",
    "Surface": "#1E1E1E",
    "Text_Primary": "#E0E0E0",
    "Text_Secondary": "#A0A0A0",
    "Accent": "#BB86FC",
    "Border_Hover": "#333333"
}
```

## 常见问题

**Q: 修改颜色后如何保存？**
A: 点击颜色按钮，在调色盘选择新颜色，自动保存到config/文件夹

**Q: 如何重置到默认颜色？**
A: 点击"重置为默认颜色"按钮

**Q: 深色和浅色主题颜色是否独立？**
A: 是的，分别保存在不同的JSON文件中

**Q: 删除config文件夹会怎样？**
A: 下次启动应用时会自动重建，使用默认颜色

**Q: 支持多个颜色预设吗？**
A: 当前支持单一自定义，可扩展为预设系统

