import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import cv2
import re
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import torch
from typing import Dict, List, Tuple, Optional, Union, Any
from collections import defaultdict
import csv
import traceback


try:
    import lpips

    LPIPS_AVAILABLE = True
except ImportError:
    LPIPS_AVAILABLE = False


class ImageComparator:

    def __init__(self, target_size=(256, 256), scale_factor=1.0, log_callback=print):
        self.target_size = target_size
        self.scale_factor = scale_factor
        self.lpips_model = None
        self.log = log_callback

    def initialize_lpips(self):
        if not LPIPS_AVAILABLE:
            self.log("LPIPS package not available. Install with 'pip install lpips'.")
            return False

        if self.lpips_model is None:
            try:
                self.log("LPIPS modelを初期化中...")
                self.lpips_model = lpips.LPIPS(net="alex").eval()
                return True
            except Exception as e:
                self.log(f"LPIPS modelの初期化に失敗: {e}")
                self.lpips_model = None
                return False
        return True

    def normalize(self, img: np.ndarray) -> np.ndarray:
        if img.min() == img.max():
            return np.zeros_like(img, dtype=np.float32)
        return (img - img.min()) / (img.max() - img.min())

    def load_and_preprocess_file(
        self, file_path: str, resize_to_target=False
    ) -> np.ndarray:
        if file_path.lower().endswith((".png", ".jpg", ".jpeg")):

            img = cv2.imread(file_path)
            if img is None:
                raise ValueError(f"画像の読み込みに失敗: {file_path}")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            img = img.astype(np.float32)
            img = self.normalize(img)

        elif file_path.lower().endswith(".csv"):

            try:
                with open(file_path, "r", newline="") as f:
                    reader = csv.reader(f)
                    data = list(reader)

                data = np.array(
                    [[float(val) for val in row] for row in data], dtype=np.float32
                )

                data = self.normalize(data)

                if len(data.shape) == 2:
                    img = np.stack([data, data, data], axis=2)
                else:
                    img = data
            except Exception as e:
                raise ValueError(f"CSVの読み込みに失敗: {file_path} - {e}")
        else:
            raise ValueError(f"サポートされていないファイル形式: {file_path}")

        if resize_to_target and img.shape[:2] != self.target_size:

            h_target, w_target = self.target_size
            h_orig, w_orig = img.shape[:2]

            h_repeat = (h_target + h_orig - 1) // h_orig
            w_repeat = (w_target + w_orig - 1) // w_orig

            resized_img = np.zeros((h_target, w_target, img.shape[2]), dtype=np.float32)
            for c in range(img.shape[2]):

                repeated = np.repeat(
                    np.repeat(img[:, :, c], h_repeat, axis=0), w_repeat, axis=1
                )
                resized_img[:, :, c] = repeated[:h_target, :w_target]

            return resized_img

        return img

    def extract_true_name(
        self, filename: str, prefix: str = "", suffix: str = ""
    ) -> str:
        name = os.path.splitext(filename)[0]

        if prefix and name.startswith(prefix):
            name = name[len(prefix) :]

        if suffix and name.endswith(suffix):
            name = name[: -len(suffix)]

        return name

    def detect_common_prefix_suffix(self, filenames: List[str]) -> Tuple[str, str]:
        if not filenames:
            return "", ""

        base_names = [os.path.splitext(f)[0] for f in filenames]

        prefix = os.path.commonprefix(base_names)

        reversed_names = [name[::-1] for name in base_names]
        rev_suffix = os.path.commonprefix(reversed_names)
        suffix = rev_suffix[::-1]

        if (
            prefix
            and suffix
            and len(prefix) + len(suffix) >= min(len(name) for name in base_names)
        ):
            return prefix, ""

        return prefix, suffix

    def calculate_metrics(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, float]:

        img1_norm = self.normalize(img1.copy())
        img2_norm = self.normalize(img2.copy())

        if img1_norm.shape != img2_norm.shape:

            if np.prod(img1_norm.shape[:2]) < np.prod(img2_norm.shape[:2]):
                h, w = img2_norm.shape[:2]
                img1_resized = np.zeros_like(img2_norm)
                for c in range(3):

                    h_repeat = (h + img1_norm.shape[0] - 1) // img1_norm.shape[0]
                    w_repeat = (w + img1_norm.shape[1] - 1) // img1_norm.shape[1]
                    temp = np.repeat(
                        np.repeat(img1_norm[:, :, c], h_repeat, axis=0),
                        w_repeat,
                        axis=1,
                    )
                    img1_resized[:, :, c] = temp[:h, :w]
                img1_norm = img1_resized
            else:
                h, w = img1_norm.shape[:2]
                img2_resized = np.zeros_like(img1_norm)
                for c in range(3):

                    h_repeat = (h + img2_norm.shape[0] - 1) // img2_norm.shape[0]
                    w_repeat = (w + img2_norm.shape[1] - 1) // img2_norm.shape[1]
                    temp = np.repeat(
                        np.repeat(img2_norm[:, :, c], h_repeat, axis=0),
                        w_repeat,
                        axis=1,
                    )
                    img2_resized[:, :, c] = temp[:h, :w]
                img2_norm = img2_resized

        metrics = {}

        try:
            metrics["psnr"] = psnr(img1_norm, img2_norm)
        except Exception as e:
            self.log(f"PSNRの計算中にエラー: {e}")
            metrics["psnr"] = float("nan")

        try:
            metrics["ssim"] = ssim(
                img1_norm, img2_norm, multichannel=True, channel_axis=2
            )
        except Exception as e:
            self.log(f"SSIMの計算中にエラー: {e}")
            metrics["ssim"] = float("nan")

        if self.lpips_model is not None:
            try:

                img1_tensor = (
                    torch.from_numpy(img1_norm).permute(2, 0, 1).unsqueeze(0) * 2 - 1
                )
                img2_tensor = (
                    torch.from_numpy(img2_norm).permute(2, 0, 1).unsqueeze(0) * 2 - 1
                )

                with torch.no_grad():
                    lpips_distance = self.lpips_model(img1_tensor, img2_tensor).item()
                    metrics["lpips"] = 1.0 - lpips_distance
            except Exception as e:
                self.log(f"LPIPSの計算中にエラー: {e}")
                metrics["lpips"] = float("nan")

        return metrics

    def compare_folders(
        self,
        folder_dict: Dict[str, str],
        output_dir: Optional[str] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:

        if "hr" in folder_dict:
            self.initialize_lpips()

        self.log(f"フォルダ比較を開始: {len(folder_dict)}個のカテゴリ")

        file_groups = defaultdict(dict)
        prefixes = {}
        suffixes = {}

        for category, folder in folder_dict.items():
            if not os.path.exists(folder):
                self.log(f"警告: フォルダが見つかりません - {folder}")
                continue

            files = [
                f
                for f in os.listdir(folder)
                if f.lower().endswith((".png", ".jpg", ".jpeg", ".csv"))
            ]

            if not files:
                self.log(f"警告: フォルダに互換性のあるファイルがありません - {folder}")
                continue

            prefix, suffix = self.detect_common_prefix_suffix(files)
            prefixes[category] = prefix
            suffixes[category] = suffix

            self.log(
                f"カテゴリ '{category}' - {len(files)}ファイル検出, 接頭辞: '{prefix}', 接尾辞: '{suffix}'"
            )

            for file in files:
                true_name = self.extract_true_name(file, prefix, suffix)
                file_groups[true_name][category] = os.path.join(folder, file)

        self.log(f"初期グループ化: {len(file_groups)}個の異なるtrueNameを検出")

        complete_groups = {}
        for true_name, category_files in file_groups.items():
            if len(category_files) == len(folder_dict):
                complete_groups[true_name] = category_files

        self.log(f"完全なグループ: {len(complete_groups)}/{len(file_groups)}")

        results = {
            "file_groups": complete_groups,
            "metrics": defaultdict(dict),
            "visualizations": {},
        }

        total_groups = len(complete_groups)
        for i, (true_name, category_files) in enumerate(complete_groups.items()):

            if progress_callback:
                progress = int((i / total_groups) * 100)
                progress_callback(progress)

            self.log(f"処理中 ({i+1}/{total_groups}): {true_name}")

            original_images = {}

            display_images = {}

            for category, file_path in category_files.items():
                try:

                    original_images[category] = self.load_and_preprocess_file(
                        file_path, resize_to_target=False
                    )

                    display_images[category] = self.load_and_preprocess_file(
                        file_path, resize_to_target=True
                    )
                except Exception as e:
                    self.log(
                        f"エラー: {true_name}の{category}画像を読み込めません: {e}"
                    )

                    zero_img = np.zeros((self.target_size[1], self.target_size[0], 3))
                    original_images[category] = zero_img
                    display_images[category] = zero_img

            if "hr" in original_images:
                hr_img = original_images["hr"]
                for category, img in original_images.items():
                    if category != "hr":
                        results["metrics"][true_name][category] = (
                            self.calculate_metrics(hr_img, img)
                        )

            vis_img = self.create_comparison_visualization(
                true_name, display_images, results["metrics"].get(true_name, {})
            )
            results["visualizations"][true_name] = vis_img

            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{true_name}_comparison.png")
                plt.imsave(output_path, vis_img)

        if output_dir and results["visualizations"]:
            all_vis = list(results["visualizations"].values())
            combined = self.create_combined_visualization(
                all_vis, os.path.join(output_dir, "all_comparisons.png")
            )

        if progress_callback:
            progress_callback(100)

        self.log(f"比較完了: {len(results['file_groups'])}個のグループを処理")
        return results

    def create_comparison_visualization(
        self,
        true_name: str,
        images: Dict[str, np.ndarray],
        metrics: Dict[str, Dict[str, float]],
    ) -> np.ndarray:
        preferred_order = ["lr", "bicubic", "hr"]

        def sort_key(category):
            if category == "lr":
                return 0
            elif category == "bicubic":
                return 1
            elif category == "hr":
                return 1000
            else:
                return 500

        categories = sorted(images.keys(), key=sort_key)

        n_images = len(categories)
        fig_width = n_images * 4
        fig_height = 5
        fig = Figure(figsize=(fig_width, fig_height), dpi=100)
        canvas = FigureCanvasAgg(fig)

        fig.suptitle(true_name, fontsize=16)

        fig.subplots_adjust(wspace=0, hspace=0, left=0, right=1, top=0.95, bottom=0.05)

        axes = []
        for i, category in enumerate(categories):
            ax = fig.add_subplot(1, n_images, i + 1)
            axes.append(ax)

            img = images[category].copy()
            if img.min() < 0 or img.max() > 1:
                img = self.normalize(img)

            ax.imshow(img)

            label_text = category

            if category in metrics:
                metric_text = f"PSNR: {metrics[category]['psnr']:.2f}\nSSIM: {metrics[category]['ssim']:.4f}"
                if "lpips" in metrics[category] and not np.isnan(
                    metrics[category]["lpips"]
                ):
                    metric_text += f"\nLPIPS: {metrics[category]['lpips']:.4f}"
                label_text += f"\n{metric_text}"

            ax.set_title(label_text)
            ax.axis("off")

        canvas.draw()
        width, height = fig.get_size_inches() * fig.get_dpi()
        image = np.frombuffer(canvas.buffer_rgba(), dtype=np.uint8).reshape(
            int(height), int(width), 4
        )

        image = image[:, :, :3]

        return image

    def create_combined_visualization(
        self, visualizations: List[np.ndarray], output_path: Optional[str] = None
    ) -> np.ndarray:
        if not visualizations:
            return np.zeros((100, 100, 3))

        max_width = max(v.shape[1] for v in visualizations)
        padded_vis = []

        for vis in visualizations:
            h, w, c = vis.shape
            if w < max_width:
                padding = np.ones((h, max_width - w, c))
                padded = np.hstack([vis, padding])
                padded_vis.append(padded)
            else:
                padded_vis.append(vis)

        combined = np.vstack(padded_vis)

        if output_path:
            plt.imsave(output_path, combined)

        return combined


if __name__ == "__main__":

    def test_log(msg):
        print(f"[TEST LOG] {msg}")

    lr_folder = "./test_images/lr"
    bicubic_folder = "./test_images/bicubic"
    sr_folder = "./test_images/sr"
    hr_folder = "./test_images/hr"
    output_dir = "./test_output"

    comparator = ImageComparator(
        target_size=(256, 256), scale_factor=1.0, log_callback=test_log
    )

    folder_dict = {
        "lr": lr_folder,
        "bicubic": bicubic_folder,
        "sr": sr_folder,
        "hr": hr_folder,
    }

    def progress_update(progress):
        print(f"Progress: {progress}%")

    try:
        results = comparator.compare_folders(
            folder_dict, output_dir, progress_callback=progress_update
        )
        print(f"Found {len(results['file_groups'])} complete groups for comparison")
    except Exception as e:
        print(f"Error during comparison: {e}")
        print(traceback.format_exc())
