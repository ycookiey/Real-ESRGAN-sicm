import os
import tkinter as tk
from tkinter import ttk
import traceback

from path_config import PathConfig
from image_comparison_ui import ImageComparisonUI
from inference_tab import InferenceTab


class RealESRGANGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RealESRGAN CSV推論・画像比較ツール")
        self.root.geometry("1100x850")

        self.path_config = PathConfig()
        self._setup_styles()

        self._create_main_widgets()

    def _setup_styles(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("Run.TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Toggle.TButton", padding=2, relief=tk.FLAT)
        self.style.map("Toggle.TButton", relief=[("active", tk.RAISED)])
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        self.style.map("TEntry", foreground=[("disabled", "gray")])
        self.style.map("TSpinbox", foreground=[("disabled", "gray")])
        self.style.map("TLabel", foreground=[("disabled", "gray")])

    def _create_main_widgets(self):

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        inference_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(inference_tab_frame, text="推論実行")
        self.inference_tab = InferenceTab(
            inference_tab_frame, self.root, self.path_config, self.log
        )

        comparison_tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(comparison_tab_frame, text="画像比較")
        self.comparison_ui = ImageComparisonUI(
            comparison_tab_frame, self.root, self.log
        )

    def log(self, message):
        if hasattr(self, "inference_tab"):
            self.inference_tab.log(message)
        else:
            print(message)

    def save_all_settings(self):
        try:

            if (
                hasattr(self.inference_tab, "exp_manager")
                and self.inference_tab.exp_manager
            ):
                self.inference_tab.exp_manager.save_data()
                print("実験データを保存しました")

            if (
                hasattr(self, "comparison_ui")
                and self.comparison_ui
                and hasattr(self.comparison_ui, "folder_selector")
                and self.comparison_ui.folder_selector
            ):
                folder_selector = self.comparison_ui.folder_selector
                custom_folders = folder_selector.custom_folders

                print(f"カスタムフォルダを保存します: {len(custom_folders)}件")
                self.path_config.save_custom_folder_history(custom_folders)
                folder_selector.save_comparison_paths()
                print("カスタムフォルダ履歴を保存しました")

            if hasattr(self.inference_tab, "save_paths"):
                self.inference_tab.save_paths()
                print("推論パス設定を保存しました")

            self.path_config.save_config(self.path_config.config)
            print("すべての設定を保存しました")

        except Exception as e:
            print(f"設定保存中にエラー: {e}")
            traceback.print_exc()


def main():
    root = tk.Tk()
    app = RealESRGANGUI(root)

    def on_closing():
        app.save_all_settings()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
