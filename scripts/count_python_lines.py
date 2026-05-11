#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计项目中的 Python 代码行数

功能：
1. 统计所有 Python 文件的总行数
2. 列出超过 300 行的 Python 文件
"""

from __future__ import annotations

import argparse
from pathlib import Path


def is_in_venv_dir(file_path: Path) -> bool:
    """判断文件是否在 .venv 或 venv 目录中"""
    for parent in file_path.parents:
        if parent.name in (".venv", "venv"):
            return True
    return False


def count_lines_in_file(file_path: Path) -> int:
    """计算单个文件的行数"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)
    except Exception as e:
        print(f"无法读取文件 {file_path}: {e}")
        return 0


def count_python_files(
    root_path: Path, ignore_tests: bool = False
) -> tuple[int, list[tuple[Path, int]]]:
    """统计所有 Python 文件的行数，并找出超过 300 行的文件

    Args:
        root_path: 项目根路径
        ignore_tests: 是否忽略测试文件（文件名以test_开头的文件）
    """
    total_lines = 0
    large_files = []

    # 使用 glob 查找所有 .py 文件
    for py_file in root_path.rglob("*.py"):
        # 跳过 .venv 和 venv 目录中的文件
        if is_in_venv_dir(py_file):
            continue

        # 如果需要忽略测试文件，且当前文件是测试文件，则跳过
        if ignore_tests and py_file.name.startswith("test_"):
            continue

        line_count = count_lines_in_file(py_file)
        total_lines += line_count

        if line_count > 300:
            large_files.append((py_file, line_count))

    return total_lines, large_files


def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="统计项目中的 Python 代码行数")
    parser.add_argument(
        "--test-ignore", action="store_true", help="忽略文件名以 test_ 开头的测试文件"
    )
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    total_lines, large_files = count_python_files(project_root, args.test_ignore)

    # 计算文件总数（根据是否忽略测试文件）
    if args.test_ignore:
        all_py_files = [
            f
            for f in project_root.rglob("*.py")
            if not f.name.startswith("test_") and not is_in_venv_dir(f)
        ]
    else:
        all_py_files = [f for f in project_root.rglob("*.py") if not is_in_venv_dir(f)]

    print(f"项目中 Python 代码总行数: {total_lines}")
    print(f"共有 {len(all_py_files)} 个 Python 文件")

    if large_files:
        print("\n超过 300 行的 Python 文件:")
        for file_path, line_count in sorted(
            large_files, key=lambda x: x[1], reverse=True
        ):
            # 计算相对路径
            relative_path = file_path.relative_to(project_root)
            print(f"  {relative_path}: {line_count} 行")
    else:
        print("\n没有超过 300 行的 Python 文件")


if __name__ == "__main__":
    main()
