import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Dict, Callable, Any


class FolderEditDialog(simpledialog.Dialog):

    def __init__(self, parent, title="フォルダ編集", initial_name="", initial_path=""):
        self.initial_name = initial_name
        self.initial_path = initial_path
        self.name_entry = None
        self.path_entry = None
        self.path_var = tk.StringVar(value=initial_path)
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        master.columnconfigure(1, weight=1)

        ttk.Label(master, text="フォルダ名:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.name_entry = ttk.Entry(master, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.name_entry.insert(0, self.initial_name)

        ttk.Label(master, text="フォルダパス:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )

        path_frame = ttk.Frame(master)
        path_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        path_frame.columnconfigure(0, weight=1)

        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=0, sticky=tk.EW)

        ttk.Button(path_frame, text="参照", command=self._browse_directory).grid(
            row=0, column=1, padx=(5, 0)
        )

        return self.name_entry

    def _browse_directory(self):
        current_path = self.path_var.get()
        initial_dir = (
            current_path if os.path.isdir(current_path) else os.path.expanduser("~")
        )

        directory = filedialog.askdirectory(
            initialdir=initial_dir, title="フォルダ選択", parent=self
        )

        if directory:
            self.path_var.set(directory)

    def apply(self):
        name = self.name_entry.get().strip()
        path = self.path_var.get().strip()

        errors = []

        if not name:
            errors.append("フォルダ名を入力してください。")

        if not path:
            errors.append("フォルダパスを入力してください。")
        elif not os.path.isdir(path):
            errors.append("有効なフォルダパスを選択してください。")

        if errors:
            messagebox.showerror("入力エラー", "\n".join(errors), parent=self)
            return

        self.result = {"name": name, "path": path}


class FolderSelector:

    def __init__(self, parent, root, log_callback, path_config):
        self.parent = parent
        self.root = root
        self.log = log_callback
        self.path_config = path_config

        self.custom_folders = {}
        self.custom_folder_checkbuttons = {}

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

        custom_folders_container = ttk.Frame(folder_frame)
        custom_folders_container.grid(
            row=len(folder_labels) + 4, column=0, columnspan=2, sticky=tk.EW, pady=5
        )
        custom_folders_container.columnconfigure(0, weight=1)

        self.folders_canvas = tk.Canvas(custom_folders_container, height=150)
        self.folders_canvas.grid(row=0, column=0, sticky="nsew")
        folders_scrollbar = ttk.Scrollbar(
            custom_folders_container,
            orient="vertical",
            command=self.folders_canvas.yview,
        )
        folders_scrollbar.grid(row=0, column=1, sticky="ns")
        self.folders_canvas.configure(yscrollcommand=folders_scrollbar.set)

        self.custom_folders_frame = ttk.Frame(self.folders_canvas)
        self.folders_canvas_window = self.folders_canvas.create_window(
            (0, 0),
            window=self.custom_folders_frame,
            anchor="nw",
            tags="self.custom_folders_frame",
        )

        self.custom_folders_frame.bind("<Configure>", self._on_frame_configure)
        self.folders_canvas.bind("<Configure>", self._on_canvas_configure)

        custom_buttons_frame = ttk.Frame(folder_frame)
        custom_buttons_frame.grid(
            row=len(folder_labels) + 5, column=0, columnspan=2, sticky=tk.EW
        )

        ttk.Button(
            custom_buttons_frame, text="削除", command=self._remove_custom_folder
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            custom_buttons_frame, text="すべて選択", command=self._select_all_folders
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            custom_buttons_frame, text="すべて解除", command=self._deselect_all_folders
        ).pack(side=tk.LEFT, padx=5)

        return folder_frame

    def _on_frame_configure(self, event):
        self.folders_canvas.configure(scrollregion=self.folders_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        width = event.width
        self.folders_canvas.itemconfig(self.folders_canvas_window, width=width)

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
        for widget in self.custom_folders_frame.winfo_children():
            widget.destroy()

        self.custom_folders.clear()
        self.custom_folder_checkbuttons.clear()

        history = self.path_config.get_custom_folder_history()
        self.log(f"カスタムフォルダ履歴を読み込み: {len(history)}件")

        for i, item in enumerate(history):
            name = item.get("name")
            path = item.get("path")
            checked = item.get("checked", True)

            if name and path:
                if os.path.isdir(path):
                    self.custom_folders[name] = {"path": path, "checked": checked}
                    self._add_folder_to_ui(name, path, checked, i)
                    self.log(
                        f"カスタムフォルダを追加: {name} -> {path} (選択状態: {checked})"
                    )
                else:
                    self.log(f"無効なパスのためスキップ: {name} -> {path}")

        if self.custom_folders:
            self.path_config.save_custom_folder_history(self.custom_folders)

    def _add_folder_to_ui(self, name, path, checked, index):
        folder_frame = ttk.Frame(self.custom_folders_frame)
        folder_frame.grid(row=index, column=0, sticky=tk.EW, pady=1)
        folder_frame.columnconfigure(0, weight=1)

        check_var = tk.BooleanVar(value=checked)

        def on_check_change():
            self.custom_folders[name]["checked"] = check_var.get()
            self.path_config.save_custom_folder_history(self.custom_folders)

        checkbutton = ttk.Checkbutton(
            folder_frame,
            variable=check_var,
            command=on_check_change,
            text=f"{name}: {path}",
        )
        checkbutton.grid(row=0, column=0, sticky=tk.W)

        def edit_this_folder():
            self._edit_specific_folder(name)

        edit_button = ttk.Button(
            folder_frame,
            text="✏",
            width=3,
            command=edit_this_folder,
        )
        edit_button.grid(row=0, column=1, padx=(5, 0), sticky=tk.E)

        def delete_this_folder():
            self._delete_specific_folder(name)

        delete_button = ttk.Button(
            folder_frame,
            text="✕",
            width=3,
            command=delete_this_folder,
        )
        delete_button.grid(row=0, column=2, padx=(2, 0), sticky=tk.E)

        self.custom_folder_checkbuttons[name] = {
            "checkbutton": checkbutton,
            "var": check_var,
            "frame": folder_frame,
            "edit_button": edit_button,
            "delete_button": delete_button,
        }

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

        self.custom_folders[name] = {"path": path, "checked": True}

        next_index = len(self.custom_folder_checkbuttons)
        self._add_folder_to_ui(name, path, True, next_index)

        self.path_config.update_custom_folder_history(name, path, True)

        self.log(f"カスタムフォルダを追加: {name} -> {path}")

        self.custom_folder_name.set("")
        self.custom_folder_path.set("")

        self.path_config.save_custom_folder_history(self.custom_folders)

        self.folders_canvas.configure(scrollregion=self.folders_canvas.bbox("all"))

    def _edit_specific_folder(self, folder_name):
        if folder_name not in self.custom_folders:
            messagebox.showerror(
                "エラー",
                f"フォルダ '{folder_name}' が見つかりません。",
                parent=self.root,
            )
            return

        current_info = self.custom_folders[folder_name]
        current_path = current_info["path"]
        current_checked = current_info["checked"]

        dialog = FolderEditDialog(
            self.root,
            title="カスタムフォルダ編集",
            initial_name=folder_name,
            initial_path=current_path,
        )

        if dialog.result is None:
            return

        new_name = dialog.result["name"]
        new_path = dialog.result["path"]

        if new_name != folder_name and (
            new_name in self.folder_vars or new_name in self.custom_folders
        ):
            messagebox.showerror(
                "エラー",
                f"フォルダ名 '{new_name}' は既に使用されています。",
                parent=self.root,
            )
            return

        if new_name != folder_name:

            del self.custom_folders[folder_name]
            self.custom_folders[new_name] = {
                "path": new_path,
                "checked": current_checked,
            }
        else:

            self.custom_folders[folder_name]["path"] = new_path

        self._refresh_folder_ui()

        self.path_config.save_custom_folder_history(self.custom_folders)

        self.log(f"カスタムフォルダを編集: {folder_name} -> {new_name}: {new_path}")

    def _delete_specific_folder(self, folder_name):
        if folder_name not in self.custom_folders:
            messagebox.showerror(
                "エラー",
                f"フォルダ '{folder_name}' が見つかりません。",
                parent=self.root,
            )
            return

        if not messagebox.askyesno(
            "確認",
            f"カスタムフォルダ '{folder_name}' を削除しますか？",
            parent=self.root,
        ):
            return

        if folder_name in self.custom_folder_checkbuttons:
            self.custom_folder_checkbuttons[folder_name]["frame"].destroy()
            del self.custom_folder_checkbuttons[folder_name]

        del self.custom_folders[folder_name]
        self._refresh_folder_ui()
        self.log(f"カスタムフォルダを削除: {folder_name}")
        self.path_config.save_custom_folder_history(self.custom_folders)

    def _edit_custom_folder(self):
        if not self.custom_folders:
            messagebox.showinfo(
                "情報", "編集するフォルダがありません。", parent=self.root
            )
            return

        folder_names = list(self.custom_folders.keys())
        selected_name = self._select_folder_dialog(
            folder_names, "編集するフォルダを選択"
        )

        if selected_name is None:
            return

        self._edit_specific_folder(selected_name)

    def _select_folder_dialog(self, folder_names, title):
        if not folder_names:
            return None

        selection_dialog = tk.Toplevel(self.root)
        selection_dialog.title(title)
        selection_dialog.transient(self.root)
        selection_dialog.grab_set()

        selection_dialog.geometry("400x300")

        selection_dialog.update_idletasks()
        x = (selection_dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (selection_dialog.winfo_screenheight() // 2) - (300 // 2)
        selection_dialog.geometry(f"400x300+{x}+{y}")

        listbox_frame = ttk.Frame(selection_dialog)
        listbox_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        listbox = tk.Listbox(listbox_frame)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            listbox_frame, orient=tk.VERTICAL, command=listbox.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=scrollbar.set)

        for name in folder_names:
            path = self.custom_folders[name]["path"]
            display_text = f"{name}: {path}"
            listbox.insert(tk.END, display_text)

        def on_double_click(event):
            on_ok()

        listbox.bind("<Double-Button-1>", on_double_click)

        button_frame = ttk.Frame(selection_dialog)
        button_frame.pack(pady=10)

        selected_name = [None]

        def on_ok():
            selected_indices = listbox.curselection()
            if selected_indices:
                selected_name[0] = folder_names[selected_indices[0]]
                selection_dialog.destroy()
            else:
                messagebox.showwarning(
                    "警告", "フォルダを選択してください。", parent=selection_dialog
                )

        def on_cancel():
            selection_dialog.destroy()

        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="キャンセル", command=on_cancel).pack(
            side=tk.LEFT
        )

        if folder_names:
            listbox.selection_set(0)
            listbox.focus_set()

        self.root.wait_window(selection_dialog)

        return selected_name[0]

    def _remove_custom_folder(self):
        if not self.custom_folders:
            messagebox.showinfo(
                "情報", "削除するフォルダがありません。", parent=self.root
            )
            return

        folder_names = list(self.custom_folders.keys())
        selected_name = self._select_folder_dialog(
            folder_names, "削除するフォルダを選択"
        )

        if selected_name is None:
            return

        self._delete_specific_folder(selected_name)

    def _refresh_folder_ui(self):
        for widget in self.custom_folders_frame.winfo_children():
            widget.destroy()

        self.custom_folder_checkbuttons.clear()

        for i, (name, folder_info) in enumerate(self.custom_folders.items()):
            path = folder_info["path"]
            checked = folder_info["checked"]
            self._add_folder_to_ui(name, path, checked, i)

        self.folders_canvas.configure(scrollregion=self.folders_canvas.bbox("all"))

    def _select_all_folders(self):
        for name, folder_info in self.custom_folders.items():
            folder_info["checked"] = True
            if name in self.custom_folder_checkbuttons:
                self.custom_folder_checkbuttons[name]["var"].set(True)

        self.path_config.save_custom_folder_history(self.custom_folders)
        self.log("すべてのカスタムフォルダを選択しました")

    def _deselect_all_folders(self):
        for name, folder_info in self.custom_folders.items():
            folder_info["checked"] = False
            if name in self.custom_folder_checkbuttons:
                self.custom_folder_checkbuttons[name]["var"].set(False)

        self.path_config.save_custom_folder_history(self.custom_folders)
        self.log("すべてのカスタムフォルダの選択を解除しました")

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

        for name, info in self.custom_folders.items():
            path = info["path"]
            checked = info["checked"]
            if checked and os.path.isdir(path):
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
