import os
import glob
import random
import shutil


def get_csv_files(input_folder):

    patterns = ["*.csv", "*.CSV", "*.Csv", "*.cSv", "*.csV", "*.CSv", "*.CsV", "*.cSV"]
    csv_files = []

    for pattern in patterns:
        csv_files.extend(glob.glob(os.path.join(input_folder, pattern)))

    csv_files = list(set(csv_files))

    return csv_files


def create_output_folders(base_folder):
    folders = {
        "train": os.path.join(base_folder, "train"),
        "val": os.path.join(base_folder, "val"),
        "test": os.path.join(base_folder, "test"),
    }

    for folder_path in folders.values():
        os.makedirs(folder_path, exist_ok=True)

    return folders


def split_files(file_list, train_ratio=16, val_ratio=4, test_ratio=5):
    total_ratio = train_ratio + val_ratio + test_ratio
    total_files = len(file_list)

    train_count = int(total_files * train_ratio / total_ratio)
    val_count = int(total_files * val_ratio / total_ratio)

    shuffled_files = file_list.copy()
    random.shuffle(shuffled_files)

    train_files = shuffled_files[:train_count]
    val_files = shuffled_files[train_count : train_count + val_count]
    test_files = shuffled_files[train_count + val_count :]

    return train_files, val_files, test_files


def copy_files(file_list, destination_folder):
    for file_path in file_list:
        filename = os.path.basename(file_path)
        destination_path = os.path.join(destination_folder, filename)
        shutil.copy2(file_path, destination_path)


def main():

    input_folder = os.getcwd()

    print(f"入力フォルダ: {input_folder}")

    csv_files = get_csv_files(input_folder)

    if not csv_files:
        print("CSVファイルが見つかりませんでした。")
        return

    print(f"見つかったCSVファイル数: {len(csv_files)}")

    output_folders = create_output_folders(input_folder)

    train_files, val_files, test_files = split_files(csv_files)

    print("ファイルをコピー中...")
    copy_files(train_files, output_folders["train"])
    copy_files(val_files, output_folders["val"])
    copy_files(test_files, output_folders["test"])

    print(
        f"分割完了: train {len(train_files)}ファイル, val {len(val_files)}ファイル, test {len(test_files)}ファイル"
    )

    print("\n詳細:")
    print(f"  train フォルダ: {output_folders['train']} ({len(train_files)} ファイル)")
    print(f"  val フォルダ: {output_folders['val']} ({len(val_files)} ファイル)")
    print(f"  test フォルダ: {output_folders['test']} ({len(test_files)} ファイル)")


if __name__ == "__main__":
    random.seed()

    main()
