# 👔 FashionClaw - AI Virtual Try-On Skill

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> Professional virtual try-on system powered by Google Gemini 3.1 Flash Image Preview. Generate high-quality images of models wearing specific clothing items using AI.

---

## ✨ Features

- **Fast Generation** - ~22 seconds per image
- **High Quality** - 896×1195 resolution output
- **Batch Processing** - Process multiple images at once
- **Multiple Modes** - Edit, style transfer, and generation
- **Detailed Reports** - Complete performance metrics

## 🖼️ Gallery

### Before & After Examples

| Model | Clothing | Result |
|:-----:|:--------:|:------:|
| ![Model 3](images/model-3.jpg) | ![Cloth 3](images/cloth-3.jpg) | ![Result 3](images/result-003.png) |
<!-- | ![Model 1](images/model-1.jpg) | ![Cloth 1](images/cloth-1.jpg) | ![Result 1](images/result-001.png) | -->
<!-- | ![Model 2](images/model-2.jpg) | ![Cloth 2](images/cloth-2.jpg) | ![Result 2](images/result-002.png) | -->

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Get API Key

1. Visit [OpenRouter](https://openrouter.ai/)
2. Sign up and get your API key
3. Set environment variable:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### Basic Usage

**Single image:**
```bash
python virtual_tryon_skill.py \
  --model images/model-1.jpg \
  --cloth images/cloth-1.jpg \
  --output result.png
```

**Batch processing:**
```bash
python batch_tryon.py
```

Edit `example_batch.json` to configure your image pairs.

<!-- ## 📖 Usage Examples

### Python API

```python
from virtual_tryon_skill import VirtualTryOnSkill

skill = VirtualTryOnSkill()

result = skill.try_on(
    model_image="model.jpg",
    cloth_image="dress.jpg",
    output_path="result.png"
)

if result["success"]:
    print(f"Generated: {result['output_path']}")
    print(f"Time: {result['generation_time']}s")
``` -->

<!-- ### Batch Processing

```python
import json
from virtual_tryon_skill import VirtualTryOnSkill

skill = VirtualTryOnSkill()

with open('batch_config.json', 'r') as f:
    config = json.load(f)

results = skill.batch_try_on(
    pairs=config["pairs"],
    output_dir=config["output_dir"]
)

for i, result in enumerate(results, 1):
    if result["success"]:
        print(f"{i}. ✅ {result['output_path']}")
``` -->

<!-- ## 📋 Configuration

### Batch Config (`batch_config.json`)

```json
{
  "pairs": [
    ["images/model-1.jpg", "images/cloth-1.jpg"],
    ["images/model-2.jpg", "images/cloth-2.jpg"]
  ],
  "output_dir": "outputs"
}
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_image` | str | Required | Path to model photo |
| `cloth_image` | str | Required | Path to clothing image |
| `output_path` | str | Auto | Output image path |
| `operation` | str | "edit" | edit, style_transfer, generate |
| `temperature` | float | 0.7 | AI creativity (0.0-1.0) | -->

## 📊 Performance

| Metric | Value |
|--------|-------|
| Generation Time | ~22 seconds/image |
| Resolution | 896×1195 pixels |
| File Size | ~1.3 MB per image |
| API Model | Gemini 3.1 Flash Image Preview |

<!-- ## 🛠️ Project Structure -->

<!-- ```
fashionclaw/
├── virtual_tryon_skill.py    # Core functionality
├── batch_tryon.py            # Batch processing
├── example_batch.json        # Example config
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── SKILL.md                  # Full documentation
├── LICENSE                   # MIT License
└── images/                   # Example images
    ├── model-*.jpg          # Model photos
    ├── cloth-*.jpg          # Clothing images
    └── result-*.png         # Generated results
``` -->

## ⚙️ Requirements

- Python 3.8+
- OpenRouter API key
- `requests`, `Pillow`, `numpy`

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

## 🔗 Links

- [OpenRouter](https://openrouter.ai/) - Get your API key
- [Gemini Documentation](https://ai.google.dev/docs)
<!-- - [Issues](https://github.com/yourusername/fashionclaw/issues) -->

---

<div align="center">

**Built with ❤️ | Powered by Google Gemini**

</div>
