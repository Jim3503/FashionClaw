#!/usr/bin/env python3
"""
OutfitAnyone 批量虚拟试穿脚本
通过 JSON 配置文件控制多对模特和服装的配对
"""

import sys
import json
from pathlib import Path

# 添加 skill 目录到 Python 路径
sys.path.insert(0, '/home/ming/.agents/skills/outfitanyone')

from virtual_tryon_skill import VirtualTryOnSkill


def main():
    """批量虚拟试穿主函数"""

    # 配置文件路径
    config_file = "/home/ming/.agents/skills/outfitanyone/example_batch.json"

    # 加载配置
    print(f"📋 加载配置文件: {config_file}")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # 提取配对信息
    pairs = config.get("pairs", [])
    output_dir = config.get("output_dir", "/home/ming/ai-projects/outfitanyone/outputs")

    print(f"\n{'='*60}")
    print(f"🎨 OutfitAnyone 批量虚拟试穿")
    print(f"{'='*60}")
    print(f"📦 配对数量: {len(pairs)}")
    print(f"📁 输出目录: {output_dir}")
    print(f"{'='*60}\n")

    # 创建 Skill 实例
    skill = VirtualTryOnSkill()

    # 批量处理
    results = skill.batch_try_on(
        pairs=pairs,
        output_dir=output_dir,
        operation="edit",
        temperature=0.7
    )

    # 统计结果
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"\n{'='*60}")
    print(f"📊 批量处理完成")
    print(f"{'='*60}")
    print(f"✅ 成功: {len(successful)}/{len(results)}")
    print(f"❌ 失败: {len(failed)}/{len(results)}")

    if successful:
        total_time = sum(r["generation_time"] for r in successful)
        avg_time = total_time / len(successful)
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        print(f"⏱️ 平均耗时: {avg_time:.2f}秒")

    # 显示详细结果
    print(f"\n📋 详细结果:")
    for i, result in enumerate(results, 1):
        if result["success"]:
            print(f"  {i}. ✅ {result['output_path']}")
        else:
            print(f"  {i}. ❌ {result['error']}")

    print(f"\n📁 报告文件: {Path(output_dir) / 'batch_report.txt'}")


if __name__ == "__main__":
    main()
