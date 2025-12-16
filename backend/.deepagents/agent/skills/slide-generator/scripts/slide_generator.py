import argparse
from PIL import Image
import os
import sys
import subprocess
from pathlib import Path

from google import genai
from google.genai import types

# Default location for Vertex AI (global for image generation models)
DEFAULT_LOCATION = "global"

def generate_image(content: str, output_dir: str, style: str = "detail", length: str = "5~", lang: str = "jp") -> None:
    """Generate image using Gemini API and save to file."""

    aspect_ratio = "16:9" # "1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9"
    resolution = "2K" # "1K", "2K", "4K"

    # Style-specific prompt enhancements
    style_prompts = {
        "detail": "A comprehensive slide deck with full text and details, perfect for emailing or viewing on its own.",
        "presentor": "Support what you say with visual slides that clearly illustrate your key points.",
    }

    with open(f"{os.path.dirname(__file__)}/image_generate_prompt.md", "r") as f:
        prompt_template = f.read()

    full_system_prompt = f"{prompt_template.format(style=style_prompts[style], length=length, lang=lang)}"

    print(f"Generating image with style '{style}'...", file=sys.stderr)

    try:
        # Use ADC (Application Default Credentials) via Vertex AI
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")  # None -> auto-detect from ADC
        location = DEFAULT_LOCATION
        client = genai.Client(
            vertexai=True,
            project=project,
            location=location
        )

        response = client.models.generate_content(
            model="gemini-3-pro-image-preview", # Nano Banana Pro
            contents=content,
            config=types.GenerateContentConfig(
                system_instruction=[full_system_prompt],
                response_modalities=["image", "text"],
                image_config=types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=resolution
                )
            )
        )

        # Extract image from response
        i = 0
        for part in response.parts:
            if part.text is not None:
                print(f"Response text: {part.text}", file=sys.stderr)
            elif part.inline_data is not None:
                image = part.as_image()
                image.save(f"{output_dir}/slide_{i}.png")
                print(f"✅ Generated: {output_dir}/slide_{i}.png", file=sys.stderr)
                i += 1
        if i == 0:
            print("Error: No image was generated in the response", file=sys.stderr)
            sys.exit(1)
        else:
            return

    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "output_dir",
        help="Output file directory (e.g., WORKING_DIR/flow/slide-generator/datetime)"
    )
    parser.add_argument(
        "--style",
        choices=["detail", "presentor"],
        default="detail",
        help="Slide Content volume (default: detail)"
    )
    parser.add_argument(
        "--length",
        choices=["1", "3", "5~"],
        default="5~",
        help="Number of slides (default: 5~)"
    )
    parser.add_argument(
        "--lang",
        choices=["jp", "en"],
        default="jp",
        help="Language (default: jp)"
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help=argparse.SUPPRESS  # 内部利用: バックグラウンドワーカー起動フラグ
    )

    args = parser.parse_args()

    with open(f"{args.output_dir}/content.md", "r") as f:
        content = f.read()

    # ワーカーとして起動された場合はそのまま実行
    if args.worker:
        generate_image(content, args.output_dir, args.style, args.length, args.lang)
        return

    # 親プロセス: バックグラウンドで自身を再起動（ワーカーモード）
    try:
        cmd = [
            sys.executable,
            str(Path(__file__).resolve()),
            args.output_dir,
            "--style",
            args.style,
            "--length",
            args.length,
            "--lang",
            args.lang,
            "--worker",
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(
            f"画像生成ジョブをバックグラウンドで開始しました (PID: {proc.pid})。"
            f" 出力先: {args.output_dir}"
        )
    except Exception as e:
        print(f"ジョブ起動に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
