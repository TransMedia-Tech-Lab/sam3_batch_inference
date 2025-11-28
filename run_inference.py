import argparse
from io import BytesIO
from pathlib import Path

import numpy as np
import requests
from PIL import Image
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

MASK_COLORS = [
    np.array([255, 0, 0], dtype=np.uint8),
    np.array([0, 255, 0], dtype=np.uint8),
    np.array([0, 128, 255], dtype=np.uint8),
    np.array([255, 255, 0], dtype=np.uint8),
    np.array([255, 0, 255], dtype=np.uint8),
    np.array([0, 255, 255], dtype=np.uint8),
]

DEFAULT_SAMPLE_URL = "https://raw.githubusercontent.com/facebookresearch/segment-anything/main/notebooks/images/truck.jpg"


def visualize_masks(image: Image.Image, mask_tensors, destination: Path) -> None:
    """Overlay every predicted mask on the image using a simple color palette."""
    img_np = np.array(image)
    overlay = img_np.copy()

    for idx, mask_tensor in enumerate(mask_tensors):
        mask_np = mask_tensor.cpu().numpy().squeeze()
        if mask_np.ndim != 2:
            continue  # Unexpected shape; skip

        color = MASK_COLORS[idx % len(MASK_COLORS)]
        overlay[mask_np > 0] = color

    alpha = 0.5
    vis_img = (img_np * (1 - alpha) + overlay * alpha).astype(np.uint8)

    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(vis_img).save(destination)


def save_individual_masks(mask_tensors, results_dir: Path, base_name: str) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    for idx, mask_tensor in enumerate(mask_tensors, start=1):
        mask_np = (mask_tensor.cpu().numpy().squeeze() > 0).astype(np.uint8) * 255
        mask_img = Image.fromarray(mask_np)
        mask_path = results_dir / f"{base_name}_mask_{idx:02d}.png"
        mask_img.save(mask_path)
        print(f"Saved mask #{idx} to {mask_path}")


def load_model():
    print("Loading SAM3 model...")
    try:
        model = build_sam3_image_model()
        processor = Sam3Processor(model)
        return processor
    except Exception as e:
        print(f"\nError loading model: {e}")
        print("\nPossible cause: You may need to authenticate with Hugging Face to download checkpoints.")
        print("Please run: huggingface-cli login")
        print("And ensure you have been granted access to the SAM3 repository: https://huggingface.co/facebook/sam3")
        return None


def collect_images(image_dir: Path):
    if not image_dir.exists() or not image_dir.is_dir():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    images = [f for f in sorted(image_dir.iterdir()) if f.suffix.lower() in VALID_EXTENSIONS]
    if not images:
        raise FileNotFoundError(f"No supported images found in {image_dir}")
    return images


def process_image(
    processor,
    image: Image.Image,
    image_name: str,
    prompt: str,
    results_dir: Path,
    save_masks: bool,
):
    inference_state = processor.set_image(image)
    output = processor.set_text_prompt(state=inference_state, prompt=prompt)
    masks = output.get("masks", [])
    scores = output.get("scores", [])

    print(f"Found {len(masks)} mask(s). Scores: {scores}")

    if len(masks) > 0:
        result_path = results_dir / f"{image_name}_result.jpg"
        visualize_masks(image, masks, result_path)
        print(f"Saved visualization (covering {len(masks)} mask(s)) to {result_path}")

        if save_masks:
            save_individual_masks(masks, results_dir, image_name)
    else:
        print("No masks found to visualize.")


def run_inference(processor, image_dir: Path, prompt: str, results_dir: Path, save_masks: bool) -> None:
    try:
        image_paths = collect_images(image_dir)
    except FileNotFoundError as exc:
        print(exc)
        return

    print(f"Processing {len(image_paths)} image(s) from {image_dir} with prompt '{prompt}'.")

    for image_path in image_paths:
        print(f"\nProcessing {image_path.name}...")
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as exc:
            print(f"Failed to load image {image_path}: {exc}")
            continue

        process_image(processor, image, image_path.stem, prompt, results_dir, save_masks)


def download_sample_image(url: str) -> Image.Image:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SAM3 inference over a folder of images.")
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("./image"),
        help="Folder that contains input images (defaults to ./image).",
    )
    parser.add_argument("--prompt", type=str, help="Text prompt used for segmentation.")
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Optional text file whose entire contents are used as the prompt.",
    )
    parser.add_argument("--results-dir", type=Path, default=Path("results"), help="Folder to store visualization outputs.")
    parser.add_argument(
        "--save-individual-masks",
        action="store_true",
        help="Also export each predicted mask as a separate grayscale PNG for debugging.",
    )
    parser.add_argument(
        "--run-sample",
        action="store_true",
        help="Download and process a reference sample image after the folder run.",
    )
    parser.add_argument(
        "--sample-url",
        type=str,
        default=DEFAULT_SAMPLE_URL,
        help="URL used when --run-sample is enabled (defaults to SAM3 demo truck).",
    )
    args = parser.parse_args()

    prompt_value = None
    if args.prompt:
        prompt_value = args.prompt
    elif args.prompt_file:
        prompt_value = args.prompt_file.read_text(encoding="utf-8").strip()
    else:
        prompt_value = input("Enter segmentation prompt: ").strip()

    if not prompt_value:
        raise ValueError("A non-empty prompt is required.")

    processor = load_model()
    if processor is None:
        raise SystemExit(1)

    run_inference(processor, args.image_dir, prompt_value, args.results_dir, args.save_individual_masks)

    if args.run_sample:
        print("\nDownloading sample image for verification...")
        try:
            sample_image = download_sample_image(args.sample_url)
            sample_name = Path(args.sample_url.split("?")[0]).stem or "sample"
            process_image(processor, sample_image, sample_name, prompt_value, args.results_dir, args.save_individual_masks)
        except Exception as exc:
            print(f"Failed to process sample URL {args.sample_url}: {exc}")
