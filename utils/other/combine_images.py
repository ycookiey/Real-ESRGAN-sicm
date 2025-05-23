#!/usr/bin/env python3


import sys
import os
from PIL import Image
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


def is_image_file(filepath):
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    return Path(filepath).suffix.lower() in image_extensions


def combine_images_vertical(image_paths, output_path="combined_vertical.png"):
    if not image_paths:
        print("エラー: 画像ファイルが指定されていません。")
        return False

    valid_images = [
        path for path in image_paths if is_image_file(path) and os.path.exists(path)
    ]

    if not valid_images:
        print("エラー: 有効な画像ファイルが見つかりません。")
        return False

    print(f"処理する画像ファイル数: {len(valid_images)}")
    for i, path in enumerate(valid_images, 1):
        print(f"{i}. {os.path.basename(path)}")

    try:

        images = []
        for path in valid_images:
            img = Image.open(path)

            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            images.append(img)

        max_width = max(img.width for img in images)

        total_height = sum(img.height for img in images)

        combined_img = Image.new("RGB", (max_width, total_height), "white")

        current_y = 0
        for img in images:

            x_offset = (max_width - img.width) // 2

            if img.mode == "RGBA":

                background = Image.new("RGB", img.size, "white")
                background.paste(img, mask=img.split()[-1])
                img = background

            combined_img.paste(img, (x_offset, current_y))
            current_y += img.height

        combined_img.save(output_path, "PNG", quality=95)
        print(f"\n✅ 画像の結合が完了しました!")
        print(f"📁 保存先: {os.path.abspath(output_path)}")
        print(f"📏 サイズ: {max_width} x {total_height} pixels")

        return True

    except Exception as e:
        print(f"❌ エラーが発生しました: {str(e)}")
        return False

    finally:

        for img in images:
            img.close()


def show_message(title, message, is_error=False):
    root = tk.Tk()
    root.withdraw()

    if is_error:
        messagebox.showerror(title, message)
    else:
        messagebox.showinfo(title, message)

    root.destroy()


def main():

    if len(sys.argv) < 2:
        show_message(
            "画像縦結合プログラム",
            "使用方法:\n"
            "1. 複数の画像ファイルをこの.pywファイルにドラッグアンドドロップしてください\n"
            "2. または付属の.batファイルを使用してください\n\n"
            "対応形式: JPG, PNG, BMP, GIF, TIFF, WebP",
            is_error=True,
        )
        return

    image_paths = sys.argv[1:]

    first_image_dir = os.path.dirname(os.path.abspath(image_paths[0]))
    output_path = os.path.join(first_image_dir, "combined_vertical.png")

    success = combine_images_vertical(image_paths, output_path)

    if success:
        show_message(
            "完了",
            f"🎉 画像の結合が完了しました!\n\n"
            f"📁 保存先: {os.path.basename(output_path)}\n"
            f"📂 場所: {first_image_dir}",
        )
    else:
        show_message("エラー", "❌ 処理中にエラーが発生しました。", is_error=True)


if __name__ == "__main__":
    main()
