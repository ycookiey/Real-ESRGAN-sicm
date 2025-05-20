import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Callable


class FolderSelector:

    def __init__(self, parent, root, log_callback, path_config):
        self.parent = parent
        self.root = root
        self.log = log_callback
        self.path_config = path_config

        self.custom_folders = {}

        self.frame = self._create_folder_frame()

        self._load_custom_folder_history()

        self._update_default_paths()

    def _create_folder_frame(self):
        folder_frame = ttk.LabelFrame(self.parent, text="画像フォルダ選択", padding=10)
        folder_frame.columnconfigure(1, weight=1)

        scale_frame = ttk.Frame(folder_frame)
        scale_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))

        ttk.Label(scale_frame, text="スケール:").pack(side=tk.LEFT, padx=(0, 10))
        self.comp_scale = tk.IntVar(value=2)
        ttk.Radiobutton(
            scale_frame,
            text="2倍",
            variable=self.comp_scale,
            value=2,
            command=self._update_default_paths,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            scale_frame,
            text="4倍",
            variable=self.comp_scale,
            value=4,
            command=self._update_default_paths,
        ).pack(side=tk.LEFT, padx=5)

        self.folder_vars = {
            "lr": tk.StringVar(),
            "bicubic": tk.StringVar(),
            "hr": tk.StringVar(),
        }

        folder_labels = {
            "lr": "低解像度 (LR):",
            "bicubic": "Bicubic補間:",
            "hr": "高解像度 (HR):",
        }

        for i, (key, label) in enumerate(folder_labels.items()):
            ttk.Label(folder_frame, text=label).grid(
                row=i + 1, column=0, sticky=tk.W, pady=2
            )
            self._create_path_entry(folder_frame, key, i + 1)

        ttk.Separator(folder_frame, orient=tk.HORIZONTAL).grid(
            row=len(folder_labels) + 1, column=0, columnspan=2, sticky="ew", pady=5
        )

        ttk.Label(folder_frame, text="カスタムフォルダ:").grid(
            row=len(folder_labels) + 2, column=0, sticky=tk.W, pady=2
        )

        self.custom_folder_name = tk.StringVar()
        self.custom_folder_path = tk.StringVar()
        custom_name_entry = ttk.Entry(
            folder_frame, textvariable=self.custom_folder_name
        )
        custom_name_entry.grid(
            row=len(folder_labels) + 2, column=1, sticky=tk.EW, pady=2
        )

        custom_folder_frame = ttk.Frame(folder_frame)
        custom_folder_frame.grid(
            row=len(folder_labels) + 3, column=0, columnspan=2, sticky=tk.EW, pady=2
        )
        custom_folder_frame.columnconfigure(0, weight=1)

        custom_folder_entry = ttk.Entry(
            custom_folder_frame, textvariable=self.custom_folder_path
        )
        custom_folder_entry.grid(row=0, column=0, sticky=tk.EW)

        ttk.Button(
            custom_folder_frame,
            text="参照",
            command=lambda: self._browse_directory(self.custom_folder_path),
        ).grid(row=0, column=1, padx=(5, 0))

        ttk.Button(
            custom_folder_frame, text="追加", command=self._add_custom_folder
        ).grid(row=0, column=2, padx=(5, 0))

        self.custom_folders_listbox = tk.Listbox(folder_frame, height=5)
        self.custom_folders_listbox.grid(
            row=len(folder_labels) + 4, column=0, columnspan=2, sticky=tk.EW, pady=5
        )

        custom_buttons_frame = ttk.Frame(folder_frame)
        custom_buttons_frame.grid(
            row=len(folder_labels) + 5, column=0, columnspan=2, sticky=tk.EW
        )

        ttk.Button(
            custom_buttons_frame, text="削除", command=self._remove_custom_folder
        ).pack(side=tk.LEFT, padx=5)

        return folder_frame

    def _create_path_entry(self, parent, key, row):
        path_frame = ttk.Frame(parent)
        path_frame.grid(row=row, column=1, sticky=tk.EW, pady=2)
        path_frame.columnconfigure(0, weight=1)

        ttk.Entry(path_frame, textvariable=self.folder_vars[key]).grid(
            row=0, column=0, sticky=tk.EW
        )
        ttk.Button(
            path_frame,
            text="参照",
            command=lambda k=key: self._browse_directory(self.folder_vars[k]),
        ).grid(row=0, column=1, padx=(5, 0))

    def _browse_directory(self, var):

        current_path = var.get()

        initial_dir = current_path

        if not os.path.isdir(initial_dir):
            latest_path = self.path_config.get_latest_custom_folder_path()
            if os.path.isdir(latest_path):
                initial_dir = latest_path
            else:

                working_dir = self.path_config.get_path("working_dir")
                initial_dir = (
                    working_dir
                    if os.path.isdir(working_dir)
                    else os.path.expanduser("~")
                )

        directory = filedialog.askdirectory(
            initialdir=initial_dir, title="ディレクトリ選択", parent=self.root
        )

        if directory:
            var.set(directory)

    def _load_custom_folder_history(self):

        self.custom_folders_listbox.delete(0, tk.END)

        self.custom_folders.clear()

        history = self.path_config.get_custom_folder_history()
        self.log(f"カスタムフォルダ履歴を読み込み: {len(history)}件")

        for item in history:
            name = item.get("name")
            path = item.get("path")
            if name and path:

                if os.path.isdir(path):
                    self.custom_folders[name] = path
                    self.custom_folders_listbox.insert(tk.END, f"{name}: {path}")
                    self.log(f"カスタムフォルダを追加: {name} -> {path}")
                else:
                    self.log(f"無効なパスのためスキップ: {name} -> {path}")

        if self.custom_folders:
            self.path_config.save_custom_folder_history(self.custom_folders)

    def _add_custom_folder(self):
        name = self.custom_folder_name.get().strip()
        path = self.custom_folder_path.get().strip()

        if not name:
            messagebox.showerror(
                "エラー", "フォルダ名を入力してください。", parent=self.root
            )
            return

        if not path or not os.path.isdir(path):
            messagebox.showerror(
                "エラー", "有効なフォルダパスを選択してください。", parent=self.root
            )
            return

        if name in self.folder_vars or name in self.custom_folders:
            messagebox.showerror(
                "エラー",
                f"フォルダ名 '{name}' は既に使用されています。",
                parent=self.root,
            )
            return

        self.custom_folders[name] = path

        self.custom_folders_listbox.insert(tk.END, f"{name}: {path}")

        self.path_config.update_custom_folder_history(name, path)

        self.log(f"カスタムフォルダを追加: {name} -> {path}")

        self.custom_folder_name.set("")
        self.custom_folder_path.set("")

        self.path_config.save_custom_folder_history(self.custom_folders)

    def _remove_custom_folder(self):
        selection = self.custom_folders_listbox.curselection()
        if not selection:
            messagebox.showinfo(
                "情報", "削除するフォルダを選択してください。", parent=self.root
            )
            return

        index = selection[0]
        item_text = self.custom_folders_listbox.get(index)
        name = item_text.split(":")[0].strip()

        if name in self.custom_folders:
            del self.custom_folders[name]
            self.custom_folders_listbox.delete(index)

    def _update_default_paths(self, *args):
        scale = self.comp_scale.get()

        scale_config = self.path_config.get_scale_config(scale)

        self.folder_vars["lr"].set(scale_config.get("lr_dir", ""))
        self.folder_vars["hr"].set(scale_config.get("hr_dir", ""))
        self.folder_vars["bicubic"].set(scale_config.get("bicubic_dir", ""))

    def get_all_folders(self):
        folder_dict = {}

        for key, var in self.folder_vars.items():
            path = var.get().strip()
            if path and os.path.isdir(path):
                folder_dict[key] = path

        for name, path in self.custom_folders.items():
            if os.path.isdir(path):
                folder_dict[name] = path

        return folder_dict

    def save_comparison_paths(self):

        scale = self.comp_scale.get()

        paths_config = {
            "lr_dir": self.folder_vars["lr"].get(),
            "hr_dir": self.folder_vars["hr"].get(),
            "bicubic_dir": self.folder_vars["bicubic"].get(),
        }

        self.path_config.update_scale_config(scale, paths_config)

        self.path_config.save_custom_folder_history(self.custom_folders)

        self.log(f"スケール {scale} の比較パス設定とカスタムフォルダ履歴を保存しました")
