import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import traceback

from image_comparator import ImageComparator


class ComparisonRunner:

    def __init__(
        self,
        parent,
        root,
        log_callback,
        folder_selector,
        parameters_panel,
        preview_panel,
    ):

        self.parent = parent
        self.root = root
        self.main_log = log_callback
        self.folder_selector = folder_selector
        self.parameters_panel = parameters_panel
        self.preview_panel = preview_panel

        self.controls_frame = self._create_controls_frame()
        self.log_frame = self._create_log_frame()

        self.comparison_thread = None

    def _create_controls_frame(self):

        controls_frame = ttk.Frame(self.parent)

        ttk.Button(
            controls_frame,
            text="比較実行",
            command=self._run_comparison,
            style="Run.TButton",
        ).pack(fill=tk.X, pady=(0, 5))

        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill=tk.X)
        ttk.Label(progress_frame, text="進捗:").pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, mode="determinate"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.RIGHT)

        return controls_frame

    def _create_log_frame(self):

        log_frame = ttk.LabelFrame(self.parent, text="ログ出力", padding=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.comparison_log = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=8
        )
        self.comparison_log.grid(row=0, column=0, sticky="nsew")
        self.comparison_log.config(state=tk.DISABLED)

        return log_frame

    def _log_message(self, message):

        if hasattr(self, "comparison_log") and self.comparison_log.winfo_exists():
            self.comparison_log.config(state=tk.NORMAL)
            self.comparison_log.insert(tk.END, str(message) + "\n")
            self.comparison_log.see(tk.END)
            self.comparison_log.config(state=tk.DISABLED)
            self.root.update_idletasks()

        self.main_log(message)

    def _run_comparison(self):

        try:

            folder_dict = self.folder_selector.get_all_folders()

            if not folder_dict:
                messagebox.showerror(
                    "エラー",
                    "少なくとも1つのフォルダを選択してください。",
                    parent=self.root,
                )
                return

            self.folder_selector.save_comparison_paths()

            output_dir = self.parameters_panel.output_dir.get().strip()
            if output_dir and not os.path.isdir(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    messagebox.showerror(
                        "エラー",
                        f"出力ディレクトリの作成に失敗しました: {e}",
                        parent=self.root,
                    )
                    return

            target_width = self.parameters_panel.target_width.get()
            target_height = self.parameters_panel.target_height.get()
            scale_factor = self.parameters_panel.scale_factor.get()

            self.preview_panel.clear_preview()

            self.progress_var.set(0)
            self.progress_label.config(text="0%")

            self.comparison_log.config(state=tk.NORMAL)
            self.comparison_log.delete(1.0, tk.END)
            self.comparison_log.config(state=tk.DISABLED)

            self._log_message("=== 画像比較実行設定 ===")
            self._log_message("フォルダ設定:")
            for name, path in folder_dict.items():
                self._log_message(f"  {name}: {path}")
            self._log_message(f"目標サイズ: {target_width}x{target_height}")
            self._log_message(f"表示倍率: {scale_factor}")
            if output_dir:
                self._log_message(f"出力ディレクトリ: {output_dir}")
            self._log_message("\n処理開始...")

            comparator = ImageComparator(
                target_size=(target_width, target_height),
                scale_factor=scale_factor,
                log_callback=self._log_message,
            )

            def update_progress(progress):
                self.progress_var.set(progress)
                self.progress_label.config(text=f"{progress}%")
                self.root.update_idletasks()

            self.comparison_thread = threading.Thread(
                target=self._run_comparison_thread,
                args=(
                    comparator,
                    folder_dict,
                    output_dir,
                    update_progress,
                    scale_factor,
                ),
            )
            self.comparison_thread.daemon = True
            self.comparison_thread.start()

        except Exception as e:
            traceback_str = traceback.format_exc()
            self._log_message(f"エラー: {e}\n{traceback_str}")
            messagebox.showerror(
                "エラー", f"比較処理中にエラーが発生しました: {e}", parent=self.root
            )

    def _run_comparison_thread(
        self, comparator, folder_dict, output_dir, progress_callback, scale_factor
    ):

        try:

            results = comparator.compare_folders(
                folder_dict, output_dir, progress_callback
            )

            self.root.after(
                0,
                lambda: self._update_comparison_results(
                    results, output_dir, scale_factor
                ),
            )

        except Exception as e:
            traceback_str = traceback.format_exc()

            self.root.after(
                0, lambda: self._log_message(f"エラー: {e}\n{traceback_str}")
            )
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "エラー", f"比較処理中にエラーが発生しました: {e}", parent=self.root
                ),
            )

    def _update_comparison_results(self, results, output_dir, scale_factor):

        try:
            file_groups = results.get("file_groups", {})
            visualizations = results.get("visualizations", {})

            if not file_groups:
                self._log_message("比較対象の画像グループが見つかりませんでした。")
                messagebox.showinfo(
                    "情報",
                    "比較対象の画像グループが見つかりませんでした。",
                    parent=self.root,
                )
                return

            self.progress_var.set(100)
            self.progress_label.config(text="100%")

            self._log_message(f"\n{len(file_groups)}個の画像グループを比較しました。")
            if output_dir:
                self._log_message(f"比較結果を {output_dir} に保存しました。")

            self.preview_panel.display_images(visualizations, scale_factor)

            self._log_message("処理完了.")

        except Exception as e:
            traceback_str = traceback.format_exc()
            self._log_message(f"結果表示中にエラー: {e}\n{traceback_str}")
            messagebox.showerror(
                "エラー", f"結果表示中にエラーが発生しました: {e}", parent=self.root
            )
