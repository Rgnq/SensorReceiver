#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
i18n 系统测试脚本
用于验证多语言支持功能是否正常工作
"""

import json
from i18n import (
    initialize_i18n, 
    t, 
    set_language, 
    get_current_language,
    get_supported_languages,
    get_language_name
)

def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}\n")

def test_initialization():
    """测试i18n初始化"""
    print_section("测试1: i18n初始化")
    initialize_i18n()
    print("✓ i18n系统初始化成功")
    
    lang = get_current_language()
    print(f"✓ 当前语言: {lang}")
    
    langs = get_supported_languages()
    print(f"✓ 支持的语言: {list(langs.keys())}")
    for code, name in langs.items():
        print(f"  - {code}: {name}")

def test_translation():
    """测试翻译功能"""
    print_section("测试2: 翻译功能")
    
    # 测试中文翻译
    print("中文翻译测试:")
    set_language('zh_CN')
    translations = [
        ("page.homepage.title", "首页"),
        ("page.settings.language", "语言"),
        ("page.settings.save_directory", "数据保存目录"),
        ("page.log.toggle", "切换"),
    ]
    
    for key, expected in translations:
        result = t(key)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {key} -> {result}")
        if result != expected:
            print(f"      期望: {expected}")
    
    # 测试英文翻译
    print("\n英文翻译测试:")
    set_language('en_US')
    translations_en = [
        ("page.homepage.title", "Home"),
        ("page.settings.language", "Language"),
        ("page.settings.save_directory", "Data Save Directory"),
        ("page.log.toggle", "Toggle"),
    ]
    
    for key, expected in translations_en:
        result = t(key)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {key} -> {result}")
        if result != expected:
            print(f"      期望: {expected}")

def test_language_switching():
    """测试语言切换"""
    print_section("测试3: 语言切换")
    
    # 切换到中文
    print("切换到中文...")
    success = set_language('zh_CN')
    if success:
        print(f"✓ 语言已切换到: {get_language_name()}")
        print(f"  当前语言代码: {get_current_language()}")
        print(f"  示例翻译: {t('page.settings.language')}")
    else:
        print("✗ 语言切换失败")
    
    # 切换到英文
    print("\n切换到英文...")
    success = set_language('en_US')
    if success:
        print(f"✓ 语言已切换到: {get_language_name()}")
        print(f"  当前语言代码: {get_current_language()}")
        print(f"  示例翻译: {t('page.settings.language')}")
    else:
        print("✗ 语言切换失败")

def test_fallback():
    """测试回退机制"""
    print_section("测试4: 不存在的键的处理")
    
    set_language('zh_CN')
    
    # 测试不存在的键
    nonexistent_key = "nonexistent.key.that.does.not.exist"
    result = t(nonexistent_key)
    
    if result == nonexistent_key:
        print(f"✓ 不存在的键返回键本身: {result}")
    else:
        print(f"✗ 不存在的键处理失败: {result}")

def test_translation_coverage():
    """测试翻译覆盖率"""
    print_section("测试5: 翻译覆盖率检查")
    
    # 加载翻译文件
    import os
    i18n_dir = "i18n"
    
    zh_file = os.path.join(i18n_dir, "zh_CN.json")
    en_file = os.path.join(i18n_dir, "en_US.json")
    
    with open(zh_file, 'r', encoding='utf-8') as f:
        zh_data = json.load(f)
    
    with open(en_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)
    
    def get_all_keys(data, prefix=""):
        """递归获取所有键"""
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                keys.extend(get_all_keys(value, full_key))
            else:
                keys.append(full_key)
        return keys
    
    zh_keys = set(get_all_keys(zh_data))
    en_keys = set(get_all_keys(en_data))
    
    print(f"中文翻译键数: {len(zh_keys)}")
    print(f"英文翻译键数: {len(en_keys)}")
    
    missing_in_en = zh_keys - en_keys
    missing_in_zh = en_keys - zh_keys
    
    if missing_in_en:
        print(f"\n⚠ 英文缺失的键 ({len(missing_in_en)}):")
        for key in sorted(missing_in_en)[:5]:
            print(f"  - {key}")
        if len(missing_in_en) > 5:
            print(f"  ... 还有 {len(missing_in_en) - 5} 个")
    else:
        print("✓ 英文翻译完整")
    
    if missing_in_zh:
        print(f"\n⚠ 中文缺失的键 ({len(missing_in_zh)}):")
        for key in sorted(missing_in_zh)[:5]:
            print(f"  - {key}")
        if len(missing_in_zh) > 5:
            print(f"  ... 还有 {len(missing_in_zh) - 5} 个")
    else:
        print("✓ 中文翻译完整")

def main():
    """运行所有测试"""
    print("\n" + "="*50)
    print("  SensorReceiver i18n 系统测试")
    print("="*50)
    
    try:
        test_initialization()
        test_translation()
        test_language_switching()
        test_fallback()
        test_translation_coverage()
        
        print_section("测试完成")
        print("✓ 所有测试执行完毕")
        print("\n更多详情，请查看 I18N_GUIDE.md")
        
    except Exception as e:
        print_section("错误")
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
