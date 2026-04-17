# 多语言本地化系统使用指南

## 概述

SensorReceiver 现已实现完整的多语言支持系统。该系统支持简体中文（zh_CN）和英文（en_US），并可轻松扩展以支持更多语言。

## 系统架构

### 文件结构
```
i18n/
  ├── zh_CN.json      # 中文翻译文件
  ├── en_US.json      # 英文翻译文件
config/
  └── language.json   # 语言偏好配置
```

### 核心模块：i18n.py

- **initialize_i18n()**: 应用启动时调用，初始化i18n系统
- **t(key)**: 获取翻译字符串的函数
- **set_language(language_code)**: 切换语言
- **get_current_language()**: 获取当前语言代码
- **get_supported_languages()**: 获取所有支持的语言

## 使用方法

### 1. 在代码中使用翻译

```python
from i18n import t

# 简单翻译
label = QLabel(t("page.homepage.title"))

# 带格式化的翻译
message = t("error.failed_to_load") + filename
```

### 2. 翻译键的命名规则

翻译键使用点号分隔的路径结构：
- `page.homepage.title` - 主页标题
- `command_panel.connect` - 命令面板连接按钮
- `color.background` - 背景色标签

结构应该反映UI的层级关系。

### 3. 添加新翻译

#### 步骤：

1. **编辑翻译文件**
   - 打开 `i18n/zh_CN.json` （中文）
   - 打开 `i18n/en_US.json` （英文）
   
2. **添加新的翻译键值对**
   ```json
   {
     "page": {
       "new_feature": {
         "button_text": "新功能按钮",
         "description": "这是一个新功能"
       }
     }
   }
   ```

3. **在代码中使用**
   ```python
   button.setText(t("page.new_feature.button_text"))
   ```

### 4. 更新UI文本（语言切换）

在 MainWindow 中，当语言改变时会自动调用 `update_ui_text()`：

```python
# 在各个页面类中实现 update_ui_text 方法
def update_ui_text(self):
    """更新所有UI文本"""
    self.button.setText(t("page.homepage.send_button"))
    self.label.setText(t("page.homepage.title"))
```

## 用户界面

### 语言选择设置

在"设置"页面中，用户可以：
1. 看到"语言"选择下拉菜单
2. 选择"简体中文"或"English"
3. 语言会立即改变（需要重启应用以应用所有更改）
4. 选择会自动保存到 `config/language.json`

## 扩展支持新语言

### 添加新语言的步骤：

1. **创建新的翻译文件**
   ```
   i18n/ja_JP.json  # 日文示例
   ```

2. **复制中文翻译文件的结构，翻译所有文本**

3. **在 i18n.py 中注册新语言**
   ```python
   _supported_languages = {
       "zh_CN": "简体中文",
       "en_US": "English",
       "ja_JP": "日本語"  # 添加新语言
   }
   ```

4. **测试新语言**

## 常见用法示例

### 示例 1: 简单标签
```python
label = QLabel(t("page.settings.save_directory"))
```

### 示例 2: 按钮
```python
button = QPushButton(t("page.settings.apply"))
```

### 示例 3: 带参数的翻译（预留功能）
```python
# 翻译字符串中包含占位符
message = t("error.failed_to_load", filename="data.csv")
```

### 示例 4: 错误处理
```python
try:
    # 某些操作
    pass
except Exception as e:
    QMessageBox.warning(self, t("error.title"), t("error.failed_to_load") + str(e))
```

## 翻译管理最佳实践

1. **保持一致性**
   - 同一概念在所有地方使用相同的翻译
   - 使用相同的翻译键

2. **组织结构**
   - 按照UI的页面和功能组织翻译键
   - 使用有意义的、自我说明的键名

3. **完整性**
   - 确保所有语言文件中都有相同的键
   - 定期检查缺失的翻译

4. **测试**
   - 在不同语言间切换时测试UI布局
   - 某些语言的文本可能比其他语言长

## 技术细节

### 翻译文件格式
- 格式：JSON
- 编码：UTF-8
- 结构：嵌套字典

### 初始化流程
1. 应用启动时调用 `initialize_i18n()`
2. 创建默认翻译文件（如果不存在）
3. 加载用户偏好的语言
4. 如果偏好不存在，默认加载中文

### 语言切换流程
1. 用户在设置中选择新语言
2. `set_language()` 被调用
3. 翻译数据被重新加载
4. 主窗口的 `update_ui_text()` 被调用
5. 所有页面的 UI 文本被更新

## 故障排除

### 问题：翻译键显示而不是文本
**解决方案**：
- 检查翻译文件中是否存在该键
- 验证键的拼写是否正确
- 确保 JSON 文件格式正确

### 问题：新语言不出现在下拉菜单中
**解决方案**：
- 检查是否在 `_supported_languages` 中注册了语言
- 确保翻译文件存在且格式正确
- 重启应用程序

### 问题：语言改变但UI文本未更新
**解决方案**：
- 确保在对应的页面类中实现了 `update_ui_text()` 方法
- 检查是否在 MainWindow 的 `update_ui_text()` 中调用了该方法
- 某些文本可能需要应用重启才能生效
