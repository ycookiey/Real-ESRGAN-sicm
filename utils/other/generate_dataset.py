import os
import shutil
import random
import glob
import numpy as np
import pandas as pd
import warnings
from PIL import Image
import matplotlib.pyplot as plt


try:
    from scipy import ndimage

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


warnings.filterwarnings("ignore")
plt.ioff()


def get_csv_files(directory):
    pattern = os.path.join(directory, "*.csv")
    csv_files = glob.glob(pattern, recursive=False)
    return [os.path.basename(f) for f in csv_files]


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"ディレクトリを作成しました: {path}")


def split_dataset(csv_files, train_ratio=16, val_ratio=4, test_ratio=5):
    total_ratio = train_ratio + val_ratio + test_ratio
    total_files = len(csv_files)

    random.shuffle(csv_files)

    train_count = int(total_files * train_ratio / total_ratio)
    val_count = int(total_files * val_ratio / total_ratio)
    test_count = total_files - train_count - val_count

    train_files = csv_files[:train_count]
    val_files = csv_files[train_count : train_count + val_count]
    test_files = csv_files[train_count + val_count :]

    return train_files, val_files, test_files


def copy_files(file_list, source_dir, dest_dir):
    create_directory(dest_dir)
    copied_count = 0

    for filename in file_list:
        source_path = os.path.join(source_dir, filename)
        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            copied_count += 1
        else:
            print(f"警告: ファイルが見つかりません: {source_path}")

    return copied_count


def csv_to_array(csv_path):
    try:

        df = pd.read_csv(csv_path, header=None)

        data = df.values.astype(np.float64)

        return data

    except Exception as e:
        print(f"CSV読み込みエラー: {csv_path}, {str(e)}")
        return None


def array_to_csv(array, csv_path):
    try:
        df = pd.DataFrame(array)
        df.to_csv(csv_path, header=False, index=False)
    except Exception as e:
        print(f"CSV保存エラー: {csv_path}, {str(e)}")


def array_to_png(array, png_path, normalize=True):
    try:

        data = array.copy()

        if normalize:

            if np.any(np.isnan(data)) or np.any(np.isinf(data)):
                print(f"警告: データにNaNまたは無限大が含まれています: {png_path}")
                data[np.isnan(data)] = 0
                data[np.isinf(data)] = 0

            min_val = np.min(data)
            max_val = np.max(data)

            if max_val > min_val:
                data = ((data - min_val) / (max_val - min_val) * 255).astype(np.uint8)
            else:
                data = np.zeros_like(data, dtype=np.uint8)
        else:

            data = np.clip(data, 0, 255).astype(np.uint8)

        img = Image.fromarray(data, mode="L")
        img.save(png_path)

    except Exception as e:
        print(f"PNG保存エラー: {png_path}, {str(e)}")


def generate_lr_patterns(hr_array, scale_factor):
    h, w = hr_array.shape[:2]
    target_h, target_w = h // scale_factor, w // scale_factor
    patterns = []

    if scale_factor == 4:
        pattern_count = 16
        for i in range(4):
            for j in range(4):

                lr_array = hr_array[i::scale_factor, j::scale_factor]
                if lr_array.shape[0] >= target_h and lr_array.shape[1] >= target_w:
                    lr_array = lr_array[:target_h, :target_w]
                    patterns.append(lr_array)
    elif scale_factor == 2:
        pattern_count = 4
        for i in range(2):
            for j in range(2):

                lr_array = hr_array[i::scale_factor, j::scale_factor]
                if lr_array.shape[0] >= target_h and lr_array.shape[1] >= target_w:
                    lr_array = lr_array[:target_h, :target_w]
                    patterns.append(lr_array)

    return patterns


def bicubic_upscale(lr_array, scale_factor):
    try:
        h, w = lr_array.shape
        new_h, new_w = h * scale_factor, w * scale_factor

        if SCIPY_AVAILABLE:

            upscaled = ndimage.zoom(lr_array, scale_factor, order=3, prefilter=False)
        else:

            y_old = np.arange(h)
            x_old = np.arange(w)
            y_new = np.linspace(0, h - 1, new_h)
            x_new = np.linspace(0, w - 1, new_w)

            upscaled = np.zeros((new_h, new_w))
            for i in range(new_h):
                for j in range(new_w):

                    y_idx = min(int(round(y_new[i])), h - 1)
                    x_idx = min(int(round(x_new[j])), w - 1)
                    upscaled[i, j] = lr_array[y_idx, x_idx]

        return upscaled

    except Exception as e:
        print(f"アップスケールエラー: {str(e)}")
        return None


def phase1_split_dataset():
    print("=" * 50)
    print("フェーズ1: 基本データセットの分割を開始します")
    print("=" * 50)

    current_dir = os.getcwd()
    print(f"作業ディレクトリ: {current_dir}")

    csv_files = get_csv_files(current_dir)

    if not csv_files:
        print("CSVファイルが見つかりません。処理を終了します。")
        return False

    print(f"見つかったCSVファイル: {len(csv_files)}個")

    train_files, val_files, test_files = split_dataset(csv_files)

    train_count = copy_files(
        train_files, current_dir, os.path.join(current_dir, "train")
    )
    val_count = copy_files(val_files, current_dir, os.path.join(current_dir, "val"))
    test_count = copy_files(test_files, current_dir, os.path.join(current_dir, "test"))

    print(
        f"\n分割完了: train {train_count}ファイル, val {val_count}ファイル, test {test_count}ファイル"
    )
    print("フェーズ1完了\n")

    return True


def phase2_generate_evaluation_datasets():
    print("=" * 50)
    print("フェーズ2: 評価用データセットの自動生成を開始します")
    print("=" * 50)

    current_dir = os.getcwd()
    test_dir = os.path.join(current_dir, "test")

    if not os.path.exists(test_dir):
        print("testディレクトリが見つかりません。フェーズ2をスキップします。")
        return

    test_csv_files = get_csv_files(test_dir)

    if not test_csv_files:
        print(
            "testディレクトリにCSVファイルが見つかりません。フェーズ2をスキップします。"
        )
        return

    print(f"処理対象ファイル: {len(test_csv_files)}個")

    output_dirs = {
        "lr_025": os.path.join(current_dir, "0.25down_sampled"),
        "lr_050": os.path.join(current_dir, "0.50down_sampled"),
        "bicubic": os.path.join(current_dir, "bicubic"),
    }

    for dir_path in output_dirs.values():
        create_directory(dir_path)

    for csv_file in test_csv_files:
        print(f"処理中: {csv_file}")
        csv_path = os.path.join(test_dir, csv_file)

        hr_array = csv_to_array(csv_path)
        if hr_array is None:
            continue

        base_name = os.path.splitext(csv_file)[0]

        print(f"  スケール4倍処理中...")
        lr_patterns_4x = generate_lr_patterns(hr_array, 4)

        for i, lr_pattern in enumerate(lr_patterns_4x):

            lr_dir = os.path.join(output_dirs["lr_025"], f"lr_test_{i}")
            create_directory(lr_dir)
            lr_path = os.path.join(lr_dir, f"{i}_{csv_file}")
            array_to_csv(lr_pattern, lr_path)

            bicubic_array = bicubic_upscale(lr_pattern, 4)
            if bicubic_array is not None:
                bicubic_dir = os.path.join(output_dirs["bicubic"], f"4x_{i}")
                create_directory(bicubic_dir)
                bicubic_path = os.path.join(bicubic_dir, f"{i}_{csv_file}")
                array_to_csv(bicubic_array, bicubic_path)

        print(f"  スケール2倍処理中...")
        lr_patterns_2x = generate_lr_patterns(hr_array, 2)

        for i, lr_pattern in enumerate(lr_patterns_2x):

            lr_dir = os.path.join(output_dirs["lr_050"], f"lr_test_{i}")
            create_directory(lr_dir)
            lr_path = os.path.join(lr_dir, f"{i}_{csv_file}")
            array_to_csv(lr_pattern, lr_path)

            bicubic_array = bicubic_upscale(lr_pattern, 2)
            if bicubic_array is not None:
                bicubic_dir = os.path.join(output_dirs["bicubic"], f"2x_{i}")
                create_directory(bicubic_dir)
                bicubic_path = os.path.join(bicubic_dir, f"{i}_{csv_file}")
                array_to_csv(bicubic_array, bicubic_path)

    print("\n評価用データセットの生成が完了しました。")
    print("フェーズ2完了\n")


def phase3_generate_validation_png_datasets():
    print("=" * 50)
    print("フェーズ3: valフォルダのPNG形式データセット生成を開始します")
    print("=" * 50)

    current_dir = os.getcwd()
    val_dir = os.path.join(current_dir, "val")

    if not os.path.exists(val_dir):
        print("valディレクトリが見つかりません。フェーズ3をスキップします。")
        return

    val_csv_files = get_csv_files(val_dir)

    if not val_csv_files:
        print(
            "valディレクトリにCSVファイルが見つかりません。フェーズ3をスキップします。"
        )
        return

    print(f"処理対象ファイル: {len(val_csv_files)}個")

    gt_png_dir = os.path.join(val_dir, "gt_png")
    lq_png_050_dir = os.path.join(val_dir, "lq_png_050")
    lq_png_025_dir = os.path.join(val_dir, "lq_png_025")

    create_directory(gt_png_dir)
    create_directory(lq_png_050_dir)
    create_directory(lq_png_025_dir)

    for csv_file in val_csv_files:
        csv_path = os.path.join(val_dir, csv_file)

        hr_array = csv_to_array(csv_path)
        if hr_array is None:
            continue

        base_name = os.path.splitext(csv_file)[0]
        png_filename = f"{base_name}.png"

        gt_png_path = os.path.join(gt_png_dir, png_filename)
        array_to_png(hr_array, gt_png_path)
        lr_patterns_2x = generate_lr_patterns(hr_array, 2)

        if lr_patterns_2x:

            lr_pattern_0 = lr_patterns_2x[0]
            lq_png_050_path = os.path.join(lq_png_050_dir, png_filename)
            array_to_png(lr_pattern_0, lq_png_050_path)
        else:
            print(f"  警告: {csv_file}の0.50倍ダウンサンプリングに失敗しました")

        lr_patterns_4x = generate_lr_patterns(hr_array, 4)

        if lr_patterns_4x:

            lr_pattern_0 = lr_patterns_4x[0]
            lq_png_025_path = os.path.join(lq_png_025_dir, png_filename)
            array_to_png(lr_pattern_0, lq_png_025_path)
        else:
            print(f"  警告: {csv_file}の0.25倍ダウンサンプリングに失敗しました")

    print(f"\nvalフォルダのPNG変換が完了しました。")
    print(f"GT PNG: {gt_png_dir}")
    print(f"0.50倍LQ PNG: {lq_png_050_dir}")
    print(f"0.25倍LQ PNG: {lq_png_025_dir}")
    print("フェーズ3完了\n")


def main():
    print("統合データセット生成スクリプト（PNG変換機能付き）を開始します")
    print(f"実行ディレクトリ: {os.getcwd()}")

    random.seed(42)
    np.random.seed(42)

    if phase1_split_dataset():

        phase2_generate_evaluation_datasets()

        phase3_generate_validation_png_datasets()

    print("=" * 50)
    print("全ての処理が完了しました！")
    print("=" * 50)


if __name__ == "__main__":
    main()
