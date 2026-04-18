#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nuitka 打包脚本 - 用于构建可执行文件
支持将 i18n 翻译文件内置到可执行文件中
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def get_project_root():
    """获取项目根目录"""
    return Path(__file__).parent

def get_build_dir():
    """获取构建输出目录"""
    return get_project_root() / "build" / "nuitka"

def get_dist_dir():
    """获取发布输出目录"""
    return get_project_root() / "dist"

def prepare_resources():
    """准备资源文件"""
    project_root = get_project_root()
    
    # 确保资源目录存在
    i18n_dir = project_root / "i18n"
    config_dir = project_root / "config"
    
    print(f"✓ i18n 目录: {i18n_dir}")
    print(f"✓ config 目录: {config_dir}")
    
    if not i18n_dir.exists():
        print(f"✗ 错误: i18n 目录不存在")
        return False
    
    return True

def build_with_nuitka(standalone=True, onefile=True, compiler="mingw64"):
    """
    使用 Nuitka 构建
    
    Args:
        standalone: 是否生成独立版本（包含所有依赖）
        onefile: 是否打包为单个可执行文件
        compiler: C 编译器 (mingw64, msvc, clang)
    """
    project_root = get_project_root()
    build_dir = get_build_dir()
    
    # 创建构建目录
    build_dir.parent.mkdir(parents=True, exist_ok=True)
    
    # Nuitka 基础参数
    cmd = [
        sys.executable,
        "-m", "nuitka",
    ]
    
    # 编译器选择
    if compiler:
        cmd.append(f"--{compiler}")
    
    # 单文件选项
    if onefile:
        cmd.append("--onefile")
    
    # 不跟踪的导入（加快构建速度）
    cmd.extend([
        "--nofollow-import-to=matplotlib",  # matplotlib 库较大，不需要跟踪
        "--follow-imports",                 # 但要跟踪其他导入
    ])
    
    # 输出目录
    cmd.extend([
        f"--output-dir={build_dir}",
        "--remove-output",  # 移除旧的输出
    ])
    
    # PySide6 相关配置
    cmd.extend([
        "--include-module=PySide6.QtOpenGL",  # 包含 OpenGL 模块
        "--enable-plugin=pyside6",            # 启用 PySide6 插件
    ])
    
    # 数据文件包含
    cmd.extend([
        "--include-data-dir=i18n=i18n",      # 包含 i18n 目录
        "--include-data-dir=config=config",  # 包含 config 目录
    ])
    
    # Windows 特定选项
    cmd.extend([
        "--windows-disable-console",  # 禁用控制台窗口
    ])
    
    # 检查图标文件是否存在
    icon_path = project_root / "icon.ico"
    if icon_path.exists():
        cmd.append(f"--windows-icon-from-ico={icon_path}")
    
    # 独立版本
    # if standalone:
    #     cmd.append("--standalone")
    
    # 显示进度和内存信息
    cmd.extend([
        "--show-progress",  # 显示构建进度
        "--show-memory",    # 显示内存使用情况
    ])
    
    # # 优化选项
    # cmd.append("-O")  # 优化级别
    
    # 主脚本
    cmd.append("main.py")
    
    print("=" * 70)
    print("Nuitka 构建命令:")
    print("=" * 70)
    print(" ".join(cmd))
    print("=" * 70)
    
    # 执行构建
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"✗ 构建失败: {e}")
        return False

def copy_to_dist(standalone=True):
    """复制构建产物到发布目录"""
    build_dir = get_build_dir()
    dist_dir = get_dist_dir()
    
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    if standalone:
        # 查找主程序目录
        main_dir = None
        for item in build_dir.iterdir():
            if item.is_dir() and "main" in item.name:
                main_dir = item
                break
        
        if not main_dir:
            # 尝试查找 .exe 文件
            exe_file = build_dir / "main.exe"
            if exe_file.exists():
                print(f"✓ 复制可执行文件: {exe_file}")
                shutil.copy2(exe_file, dist_dir / "SensorReceiver.exe")
                return True
            else:
                print("✗ 未找到构建产物")
                return False
        
        # 复制整个目录
        dist_main = dist_dir / "SensorReceiver"
        if dist_main.exists():
            shutil.rmtree(dist_main)
        
        shutil.copytree(main_dir, dist_main)
        print(f"✓ 已复制到: {dist_main}")
        return True
    
    return False

def verify_package(exe_path):
    """验证打包的可执行文件"""
    if not exe_path.exists():
        print(f"✗ 可执行文件不存在: {exe_path}")
        return False
    
    print(f"\n✓ 可执行文件已生成: {exe_path}")
    print(f"  文件大小: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    
    return True

def main():
    """主构建流程"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Nuitka 打包脚本")
    parser.add_argument("--standalone", action="store_true", default=True,
                       help="构建独立版本（包含依赖）")
    parser.add_argument("--onefile", action="store_true", default=False,
                       help="打包为单个可执行文件")
    parser.add_argument("--no-copy", action="store_true", default=False,
                       help="不复制到 dist 目录")
    parser.add_argument("--compiler", choices=["mingw64", "msvc", "clang"], default="mingw64",
                       help="C 编译器选择 (默认: mingw64)")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("  SensorReceiver Nuitka 打包")
    print("=" * 70 + "\n")
    
    # 步骤1: 准备资源
    print("[1/4] 检查资源文件...")
    if not prepare_resources():
        return 1
    print()
    
    # 步骤2: 构建
    print("[2/4] 使用 Nuitka 构建 (编译器: {})...".format(args.compiler))
    if not build_with_nuitka(standalone=args.standalone, onefile=args.onefile, compiler=args.compiler):
        return 1
    print()
    
    # 步骤3: 复制到发布目录
    print("[3/4] 复制到发布目录...")
    if not args.no_copy and not copy_to_dist(standalone=args.standalone):
        return 1
    print()
    
    # 步骤4: 验证
    print("[4/4] 验证打包...")
    dist_dir = get_dist_dir()
    exe_path = dist_dir / "SensorReceiver.exe"
    
    if verify_package(exe_path):
        print("\n" + "=" * 70)
        print("  ✅ 打包成功！")
        print("=" * 70)
        print(f"\n可执行文件位置: {exe_path}")
        print(f"包含目录位置: {dist_dir}\n")
        return 0
    else:
        print("\n" + "=" * 70)
        print("  ⚠ 验证警告")
        print("=" * 70)
        return 0

if __name__ == "__main__":
    sys.exit(main())
