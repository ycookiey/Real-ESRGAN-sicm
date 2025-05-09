import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Dict, Any, Optional


from constants import EXPERIMENT_DATA_FILE, EXPERIMENT_COLUMNS, EXPERIMENT_COLUMN_NAMES


class ExperimentEditDialog(simpledialog.Dialog):

    def __init__(self, parent, title="実験設定編集", initial_values=None):
        self.columns = EXPERIMENT_COLUMNS
        self.column_names = EXPERIMENT_COLUMN_NAMES
        self.initial_values = (
            initial_values if initial_values else {col: "" for col in self.columns}
        )
        self.entries = {}
        super().__init__(parent, title)

    def body(self, master):
        master.columnconfigure(1, weight=1)
        for i, col_key in enumerate(self.columns):
            label_text = self.column_names[i]
            ttk.Label(master, text=f"{label_text}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            entry = ttk.Entry(master, width=25)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=2)
            entry.insert(0, str(self.initial_values.get(col_key, "")))
            self.entries[col_key] = entry
            if col_key == "version" and self.initial_values.get("version"):
                entry.config(state=tk.DISABLED)

        first_editable_entry = (
            self.entries.get("version")
            if not self.initial_values.get("version")
            else self.entries.get("total_iter")
        )
        if first_editable_entry:
            return first_editable_entry
        return None

    def apply(self):
        self.result = {}
        errors = []
        for i, col_key in enumerate(self.columns):
            entry = self.entries[col_key]
            value = entry.get().strip()
            col_name = self.column_names[i]

            if col_key in [
                "total_iter",
                "model_save_freq",
                "batch_size",
                "num_train_images",
                "best_iter",
            ]:
                if value:
                    try:

                        if col_key == "best_iter" and not value:
                            self.result[col_key] = ""
                            continue
                        num_value = int(value)
                        if num_value < 0:
                            errors.append(
                                f"{col_name}: 0以上の整数を入力してください。"
                            )
                        else:
                            self.result[col_key] = num_value
                    except ValueError:
                        errors.append(f"{col_name}: 有効な整数を入力してください。")
                        self.result[col_key] = value
                else:
                    if col_key != "best_iter":
                        errors.append(f"{col_name}: 値を入力してください。")
                        self.result[col_key] = ""
                    else:
                        self.result[col_key] = ""
            elif col_key == "version":
                if not value:
                    errors.append(f"{col_name}: 値を入力してください。")
                self.result[col_key] = value
            else:
                self.result[col_key] = value

        if errors:
            messagebox.showerror("入力エラー", "\n".join(errors), parent=self)
            self.result = None
            return

        if (
            self.initial_values.get("version")
            and self.entries["version"].cget("state") == tk.DISABLED
        ):
            self.result["version"] = self.initial_values["version"]


class ExperimentManager:

    def __init__(self, treeview_widget, parent_window, log_callback):
        self.tree = treeview_widget
        self.parent_window = parent_window
        self.log = log_callback
        self.data_file = EXPERIMENT_DATA_FILE
        self.columns = EXPERIMENT_COLUMNS
        self.column_names = EXPERIMENT_COLUMN_NAMES
        self.experiment_data: List[Dict[str, Any]] = []
        self._configure_treeview()
        self.load_data()

    def _configure_treeview(self):

        self.tree.configure(columns=self.columns, show="headings")
        for i, col_key in enumerate(self.columns):
            col_name = self.column_names[i]

            width = (
                120 if col_key == "best_iter" else (70 if col_key == "version" else 85)
            )
            self.tree.heading(col_key, text=col_name, anchor=tk.W)
            self.tree.column(col_key, width=width, anchor=tk.W, stretch=False)

    def load_data(self):

        self.experiment_data = []
        if not os.path.exists(self.data_file):
            self.log(
                f"情報: '{self.data_file}' が見つかりません。サンプルデータで作成します。"
            )

            self.experiment_data = [
                {
                    "version": "1.0.0",
                    "total_iter": 1000,
                    "model_save_freq": 10,
                    "batch_size": 12,
                    "num_train_images": 309,
                    "best_iter": 900,
                },
                {
                    "version": "3.1.2",
                    "total_iter": 100000,
                    "model_save_freq": 100,
                    "batch_size": 12,
                    "num_train_images": 398,
                    "best_iter": 85000,
                },
            ]
            self.save_data()
            return

        try:
            with open(self.data_file, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                if set(reader.fieldnames if reader.fieldnames else []) != set(
                    self.columns
                ):
                    messagebox.showwarning(
                        "データ形式エラー",
                        f"'{self.data_file}' の列が異なります。\n期待: {self.columns}\n実際: {reader.fieldnames}\nデータを読み込めませんでした。",
                        parent=self.parent_window,
                    )
                    return

                for row_num, row in enumerate(reader, 1):
                    entry = {}
                    valid_entry = True

                    if not all(col in row for col in self.columns):
                        self.log(
                            f"警告: 行 {row_num} は列が不足しています。スキップします。"
                        )
                        continue

                    for col in self.columns:
                        value = row.get(col, "")
                        if col in [
                            "total_iter",
                            "model_save_freq",
                            "batch_size",
                            "num_train_images",
                            "best_iter",
                        ]:
                            if value:
                                try:
                                    entry[col] = int(value)
                                except ValueError:

                                    if col == "best_iter" and value == "":
                                        entry[col] = ""
                                    else:
                                        self.log(
                                            f"警告: 行 {row_num}, 列 '{col}' の値 '{value}' は不正な整数です。スキップします。"
                                        )
                                        valid_entry = False
                                        break
                            else:
                                entry[col] = "" if col == "best_iter" else 0
                        else:
                            entry[col] = value
                    if valid_entry:
                        self.experiment_data.append(entry)

            self.experiment_data.sort(
                key=lambda x: tuple(map(int, x.get("version", "0.0.0").split(".")))
            )
            self.log(
                f"情報: '{self.data_file}' から {len(self.experiment_data)} 件のデータを読み込みました。"
            )
        except Exception as e:
            messagebox.showerror(
                "データ読込エラー",
                f"'{self.data_file}' の読み込み中にエラー:\n{e}",
                parent=self.parent_window,
            )

    def save_data(self):

        try:

            self.experiment_data.sort(
                key=lambda x: tuple(map(int, x.get("version", "0.0.0").split(".")))
            )
            with open(self.data_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns)
                writer.writeheader()
                writer.writerows(self.experiment_data)
            self.log(f"情報: 実験データを '{self.data_file}' に保存しました。")
        except Exception as e:
            messagebox.showerror(
                "データ保存エラー",
                f"'{self.data_file}' への保存中にエラー:\n{e}",
                parent=self.parent_window,
            )

    def populate_treeview(self):

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, entry in enumerate(self.experiment_data):
            values = [entry.get(col, "") for col in self.columns]
            self.tree.insert("", tk.END, iid=f"row_{i}", values=values)

    def get_selected_data(self) -> Optional[Dict[str, Any]]:

        selected_items = self.tree.selection()
        if not selected_items:
            return None
        selected_iid = selected_items[0]
        try:

            selected_index = int(selected_iid.split("_")[1])
            if 0 <= selected_index < len(self.experiment_data):
                return self.experiment_data[selected_index]
            else:
                self.log(
                    f"エラー: 不正なインデックス {selected_index} (iid: {selected_iid})"
                )
                return None
        except (IndexError, ValueError) as e:
            self.log(f"エラー: 選択データの取得に失敗 (iid: {selected_iid}): {e}")
            return None

    def get_data_by_version(self, version: str) -> Optional[Dict[str, Any]]:

        for data in self.experiment_data:
            if data.get("version") == version:
                return data
        return None

    def get_all_data(self) -> List[Dict[str, Any]]:

        return self.experiment_data

    def add_entry(self):

        dialog = ExperimentEditDialog(self.parent_window, title="実験設定追加")
        if dialog.result:
            new_data = dialog.result
            existing_versions = {d.get("version") for d in self.experiment_data}
            if new_data.get("version") in existing_versions:
                messagebox.showerror(
                    "重複エラー",
                    f"バージョン '{new_data.get('version')}' は既に使用されています。",
                    parent=self.parent_window,
                )
                return

            self.experiment_data.append(new_data)
            self.populate_treeview()

            last_item_iid = f"row_{len(self.experiment_data) - 1}"
            if self.tree.exists(last_item_iid):
                self.tree.selection_set(last_item_iid)
                self.tree.focus(last_item_iid)
                self.tree.see(last_item_iid)

    def edit_entry(self):

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "情報", "編集する行を選択してください。", parent=self.parent_window
            )
            return

        selected_iid = selected_items[0]
        try:
            selected_index = int(selected_iid.split("_")[1])
            if not (0 <= selected_index < len(self.experiment_data)):
                raise IndexError("Index out of bounds")
            initial_data = self.experiment_data[selected_index]

            dialog = ExperimentEditDialog(
                self.parent_window, title="実験設定編集", initial_values=initial_data
            )
            if dialog.result:
                self.experiment_data[selected_index] = dialog.result
                self.populate_treeview()

                if self.tree.exists(selected_iid):
                    self.tree.selection_set(selected_iid)
                    self.tree.focus(selected_iid)
        except (IndexError, ValueError) as e:
            messagebox.showerror(
                "エラー", f"選択行データの取得/編集失敗: {e}", parent=self.parent_window
            )

    def delete_entry(self):

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "情報", "削除する行を選択してください。", parent=self.parent_window
            )
            return

        selected_iid = selected_items[0]
        try:
            selected_index = int(selected_iid.split("_")[1])
            if not (0 <= selected_index < len(self.experiment_data)):
                raise IndexError("Index out of bounds")
            version_to_delete = self.experiment_data[selected_index].get("version")

            if messagebox.askyesno(
                "確認",
                f"バージョン '{version_to_delete}' の設定を削除しますか？",
                parent=self.parent_window,
            ):
                del self.experiment_data[selected_index]
                self.populate_treeview()
        except (IndexError, ValueError) as e:
            messagebox.showerror(
                "エラー", f"選択行データの取得/削除失敗: {e}", parent=self.parent_window
            )

    def select_first_item(self):

        children = self.tree.get_children()
        if children:
            first_item_iid = children[0]
            self.tree.selection_set(first_item_iid)
            self.tree.focus(first_item_iid)
            return first_item_iid
        return None
