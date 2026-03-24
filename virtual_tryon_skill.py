#!/usr/bin/env python3
"""
OutfitAnyone Virtual Try-On Skill
基于 Gemini 3.1 Flash Image Preview 的专业虚拟试穿系统
"""

import argparse
import base64
import json
import os
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from PIL import Image
import numpy as np


# ==================== 配置管理 ====================

class SkillConfig:
    """Skill配置管理"""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.outfitanyone"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"

    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "api_key": "",
            "base_url": "https://openrouter.ai/api/v1",
            "model": "google/gemini-3.1-flash-image-preview",
            "default_output_dir": "outputs",
            "max_image_size": 2048
        }

    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)

    def get_api_key(self) -> str:
        """获取API Key"""
        # 优先从环境变量
        env_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if env_key:
            return env_key

        # 从配置文件
        config = self.load_config()
        config_key = config.get("api_key", "").strip()
        if config_key:
            return config_key

        raise RuntimeError(
            "❌ 未找到 API Key！\n"
            "请设置环境变量: export OPENROUTER_API_KEY='your_key'\n"
            "或者在首次运行时输入 API Key"
        )

    def update_api_key(self, api_key: str) -> None:
        """更新API Key"""
        config = self.load_config()
        config["api_key"] = api_key
        self.save_config(config)


# ==================== 核心虚拟试穿类 ====================

class VirtualTryOnSkill:
    """OutfitAnyone 虚拟试穿 Skill"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.config_manager = SkillConfig()
        self.api_key = api_key or self.config_manager.get_api_key()
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.model = model or "google/gemini-3.1-flash-image-preview"

        # 创建默认输出目录
        config = self.config_manager.load_config()
        self.output_dir = Path(config.get("default_output_dir", "outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_image(self, image_path: str, max_size: int = 2048) -> Dict[str, Any]:
        """准备图片用于API调用"""
        if not Path(image_path).exists():
            raise FileNotFoundError(f"❌ 图片不存在: {image_path}")

        img = Image.open(image_path)

        # 转换为RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # 调整大小
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)

        # 转换为base64
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        return {
            "inline_data": {
                "mime_type": "image/png",
                "data": base64.b64encode(img_bytes).decode('utf-8')
            }
        }

    def build_prompt(self, operation: str = "edit") -> str:
        """构建专业的虚拟试穿提示词"""
        if operation == "edit":
            return (
                "Create a professional virtual try-on image. "
                "Apply the clothing design from the second image onto the person in the first image. "
                "Maintain the person's pose, body shape, facial features, and overall appearance. "
                "Only replace the clothing while keeping everything else realistic and natural. "
                "Focus on proper fit, fabric texture, folds, wrinkles, and natural lighting. "
                "This is for professional fashion design and e-commerce visualization."
            )
        elif operation == "style_transfer":
            return (
                "Apply the style and design elements from the clothing image to create a new fashion visualization. "
                "Blend the clothing aesthetics naturally while maintaining professional quality."
            )
        else:
            return "Generate a professional fashion design visualization combining the provided images."

    def call_api(self, prompt: str, encoded_images: List[Dict], temperature: float = 0.7) -> Tuple[List[bytes], str]:
        """调用OpenRouter API"""
        try:
            # 构建消息内容
            content_parts = [{"type": "text", "text": prompt}]

            for img_data in encoded_images:
                base64_data = img_data["inline_data"]["data"]
                mime_type = img_data["inline_data"]["mime_type"]
                data_url = f"data:{mime_type};base64,{base64_data}"
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": data_url}
                })

            # 构建负载
            payload = {
                "model": self.model,
                "messages": [{
                    "role": "user",
                    "content": content_parts
                }],
                "max_tokens": 4096,
                "modalities": ["text", "image"]
            }

            # 条件性添加temperature
            if "gpt-5" not in self.model:
                payload["temperature"] = temperature

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://outfitanyone.local",
                "X-Title": "OutfitAnyone Virtual Try-On"
            }

            # API调用
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=120
            )

            response.raise_for_status()
            result = response.json()

            # 提取图片
            images = self.extract_images(result)

            return images, "API调用成功"

        except Exception as e:
            return [], f"API调用失败: {str(e)}"

    def extract_images(self, response: Dict) -> List[bytes]:
        """从响应中提取图片"""
        images = []

        try:
            choices = response.get("choices", [])
            if not choices:
                return images

            message = choices[0].get("message", {})

            # 首先尝试从 images 字段提取（OpenRouter 格式）
            if "images" in message:
                for img_data in message["images"]:
                    url = None
                    if isinstance(img_data, dict):
                        # 直接获取 url
                        if 'url' in img_data:
                            url = img_data['url']
                        # 从 image_url 中获取
                        elif 'image_url' in img_data:
                            image_url_obj = img_data['image_url']
                            if isinstance(image_url_obj, dict) and 'url' in image_url_obj:
                                url = image_url_obj['url']
                            elif isinstance(image_url_obj, str):
                                url = image_url_obj

                    if url and url.startswith("data:image"):
                        try:
                            header, b64_data = url.split(",", 1)
                            image_binary = base64.b64decode(b64_data)
                            images.append(image_binary)
                        except Exception as e:
                            print(f"⚠️ 解码图片失败: {e}")
                            continue

            # 兼容旧格式：从 content 字段提取
            elif message.get("content"):
                content = message.get("content")
                if isinstance(content, list):
                    for item in content:
                        if item.get("type") == "image_url":
                            url = item.get("image_url", {}).get("url", "")
                            if url.startswith("data:image"):
                                try:
                                    header, b64_data = url.split(",", 1)
                                    image_binary = base64.b64decode(b64_data)
                                    images.append(image_binary)
                                except Exception:
                                    pass

        except Exception as e:
            print(f"⚠️ 图片提取失败: {e}")

        return images

    def try_on(self,
               model_image: str,
               cloth_image: str,
               output_path: str = None,
               operation: str = "edit",
               temperature: float = 0.7) -> Dict[str, Any]:
        """执行虚拟试穿

        Args:
            model_image: 模特图片路径
            cloth_image: 服装图片路径
            output_path: 输出图片路径（可选）
            operation: 操作类型 (edit/style_transfer/generate)
            temperature: AI创造度 (0.0-1.0)

        Returns:
            包含结果信息的字典
        """
        result = {
            "success": False,
            "output_path": None,
            "generation_time": 0,
            "file_size": 0,
            "image_size": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # 1. 准备图片
            print("📸 准备图片...")
            model_img = self.prepare_image(model_image)
            cloth_img = self.prepare_image(cloth_image)

            # 2. 构建提示词
            print("💭 构建提示词...")
            prompt = self.build_prompt(operation)

            # 3. 调用API
            print("🔄 调用 AI 模型...")
            start_time = time.time()

            encoded_images = [model_img, cloth_img]
            images, log = self.call_api(prompt, encoded_images, temperature)

            end_time = time.time()
            result["generation_time"] = round(end_time - start_time, 2)

            # 4. 处理结果
            if not images:
                result["error"] = "未生成任何图片"
                return result

            # 生成输出路径
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = self.output_dir / f"tryon_{timestamp}.png"

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存图片
            img_binary = images[0]
            image = Image.open(BytesIO(img_binary))

            if image.mode != "RGB":
                image = image.convert("RGB")

            image.save(output_path)

            result.update({
                "success": True,
                "output_path": str(output_path),
                "file_size": output_path.stat().st_size,
                "image_size": image.size
            })

            print(f"✅ 虚拟试穿完成!")
            print(f"📁 保存到: {output_path}")
            print(f"⏱️ 耗时: {result['generation_time']}秒")
            print(f"📊 大小: {result['file_size'] / 1024:.1f} KB")
            print(f"🖼️ 尺寸: {result['image_size']}")

            return result

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 虚拟试穿失败: {str(e)}")
            return result

    def batch_try_on(self,
                     pairs: List[Tuple[str, str]],
                     output_dir: str = None,
                     **kwargs) -> List[Dict[str, Any]]:
        """批量虚拟试穿

        Args:
            pairs: [(模特图, 服装图), ...] 的列表
            output_dir: 输出目录
            **kwargs: 传递给try_on的其他参数

        Returns:
            结果列表
        """
        results = []
        output_base = Path(output_dir or self.output_dir / "batch")
        output_base.mkdir(parents=True, exist_ok=True)

        for i, (model_img, cloth_img) in enumerate(pairs, 1):
            print(f"\n{'='*60}")
            print(f"处理 {i}/{len(pairs)}")
            print(f"{'='*60}")

            output_path = output_base / f"result_{i:03d}.png"
            result = self.try_on(model_img, cloth_img, str(output_path), **kwargs)
            results.append(result)

            # 避免API限流
            if i < len(pairs):
                time.sleep(2)

        # 生成报告
        self._generate_batch_report(results, output_base)

        return results

    def _generate_batch_report(self, results: List[Dict], output_dir: Path) -> None:
        """生成批量处理报告"""
        report_path = output_dir / "batch_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("OutfitAnyone 批量虚拟试穿报告\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总任务数: {len(results)}\n\n")

            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]

            f.write(f"✅ 成功: {len(successful)}\n")
            f.write(f"❌ 失败: {len(failed)}\n\n")

            if successful:
                avg_time = sum(r["generation_time"] for r in successful) / len(successful)
                f.write(f"平均耗时: {avg_time:.2f}秒\n")
                f.write(f"总耗时: {sum(r['generation_time'] for r in successful):.2f}秒\n\n")

            f.write("=" * 80 + "\n")
            f.write("详细结果\n")
            f.write("=" * 80 + "\n\n")

            for i, result in enumerate(results, 1):
                f.write(f"{i}. 任务结果\n")
                if result["success"]:
                    f.write(f"   状态: ✅ 成功\n")
                    f.write(f"   输出: {result['output_path']}\n")
                    f.write(f"   耗时: {result['generation_time']}秒\n")
                    f.write(f"   大小: {result['file_size'] / 1024:.1f} KB\n")
                    f.write(f"   尺寸: {result['image_size']}\n")
                else:
                    f.write(f"   状态: ❌ 失败\n")
                    f.write(f"   错误: {result['error']}\n")
                f.write("\n")

        print(f"\n📋 批量报告已保存到: {report_path}")


# ==================== 命令行接口 ====================

def main():
    """命令行主入口"""
    parser = argparse.ArgumentParser(
        description="OutfitAnyone - 专业虚拟试穿系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法
  python virtual_tryon_skill.py --model model.jpg --cloth cloth.jpg

  # 指定输出路径
  python virtual_tryon_skill.py --model model.jpg --cloth cloth.jpg --output result.png

  # 批量处理
  python virtual_tryon_skill.py --batch pairs.json --output-dir results/

  # 风格迁移模式
  python virtual_tryon_skill.py --model model.jpg --cloth cloth.jpg --operation style_transfer
        """
    )

    parser.add_argument("--model", help="模特图片路径")
    parser.add_argument("--cloth", help="服装图片路径")
    parser.add_argument("--output", help="输出图片路径")
    parser.add_argument("--operation", default="edit",
                       choices=["edit", "style_transfer", "generate"],
                       help="操作类型 (默认: edit)")
    parser.add_argument("--temperature", type=float, default=0.7,
                       help="AI创造度 0.0-1.0 (默认: 0.7)")
    parser.add_argument("--batch", help="批量处理配置文件(JSON)")
    parser.add_argument("--output-dir", help="批量处理输出目录")
    parser.add_argument("--api-key", help="OpenRouter API Key")
    parser.add_argument("--model-name", default="google/gemini-3.1-flash-image-preview",
                       help="AI模型名称")

    args = parser.parse_args()

    # 创建Skill实例
    try:
        skill = VirtualTryOnSkill(
            api_key=args.api_key,
            model=args.model_name
        )

        # 批量处理模式
        if args.batch:
            print("🚀 OutfitAnyone 批量虚拟试穿模式")

            # 读取批量配置
            with open(args.batch, 'r') as f:
                batch_config = json.load(f)

            pairs = batch_config.get("pairs", [])
            if not pairs:
                print("❌ 批量配置文件格式错误")
                return

            results = skill.batch_try_on(
                pairs=pairs,
                output_dir=args.output_dir,
                operation=args.operation,
                temperature=args.temperature
            )

            # 打印总结
            successful = len([r for r in results if r["success"]])
            print(f"\n🎉 批量处理完成: {successful}/{len(results)} 成功")

        # 单张处理模式
        elif args.model and args.cloth:
            print("🚀 OutfitAnyone 虚拟试穿系统")
            print(f"👔 模特: {args.model}")
            print(f"👗 服装: {args.cloth}")
            print(f"🎭 模式: {args.operation}")
            print(f"🌡️ 创造度: {args.temperature}")

            result = skill.try_on(
                model_image=args.model,
                cloth_image=args.cloth,
                output_path=args.output,
                operation=args.operation,
                temperature=args.temperature
            )

            if result["success"]:
                print(f"\n🎉 虚拟试穿成功!")
                print(f"📁 结果: {result['output_path']}")
            else:
                print(f"\n❌ 虚拟试穿失败: {result['error']}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"❌ 系统错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
