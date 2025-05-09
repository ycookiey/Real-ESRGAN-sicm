import os
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import traceback
from typing import Optional, Dict, Any, List


from constants import SCALE_CONFIGS_DEFAULT
from experiment_manager import (
    ExperimentManager,
)
from inference_runner import run_realesrgan_inference
from path_config import PathConfig


class RealESRGANGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RealESRGAN CSV推論ツール (設定管理付き)")
        self.root.geometry("1100x850")

        self.path_config = PathConfig()

        self.style = ttk.Style()
        self.style.configure("TButton", padding=5)
        self.style.configure("Run.TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Toggle.TButton", padding=2, relief=tk.FLAT)
        self.style.map("Toggle.TButton", relief=[("active", tk.RAISED)])
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))

        self.style.map("TEntry", foreground=[("disabled", "gray")])
        self.style.map("TSpinbox", foreground=[("disabled", "gray")])
        self.style.map("TLabel", foreground=[("disabled", "gray")])

        self.config_display = {
            "version": tk.StringVar(),
            "total_iter": tk.IntVar(),
            "model_save_freq": tk.IntVar(),
        }

        self.config_manual = {
            "experiment_name": tk.StringVar(value="finetune_csv_x4_3.1.2"),
            "pattern_num": tk.IntVar(value=0),
            "model_name": tk.StringVar(value="RealESRGAN_x4plus"),
            "scale": tk.IntVar(value=2),
            "execution_mode": tk.StringVar(value="range"),
            "target_iteration": tk.IntVar(),
            "experiments_dir": tk.StringVar(
                value=self.path_config.get_path("experiments_dir")
            ),
            "csv_input_dir": tk.StringVar(),
            "csv_output_dir": tk.StringVar(),
            "python_path": tk.StringVar(value=self.path_config.get_path("python_path")),
            "working_dir": tk.StringVar(value=self.path_config.get_path("working_dir")),
        }

        self.widgets = {}
        self.options_visible = tk.BooleanVar(value=False)

        self.create_widgets()

        self.config_manual["scale"].trace_add("write", self.on_scale_change)
        self.config_manual["execution_mode"].trace_add(
            "write", self.toggle_parameter_state
        )

        self.on_scale_change()
        self.toggle_parameter_state()

        first_item_iid = self.exp_manager.select_first_item()
        if first_item_iid:
            self.on_treeview_select(None)

    def create_widgets(self):

        settings_container = ttk.Frame(self.root, padding=5)
        settings_container.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
        execution_container = ttk.Frame(self.root, padding=5)
        execution_container.pack(
            side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5)
        )

        self.create_settings_widgets(settings_container)

        self.create_execution_widgets(execution_container)

    def create_settings_widgets(self, parent_container):

        settings_outer_frame = ttk.Frame(parent_container)
        settings_outer_frame.pack(fill=tk.X, expand=False)

        treeview_frame = ttk.LabelFrame(
            settings_outer_frame, text="実験設定リスト", padding=5
        )
        treeview_frame.pack(fill=tk.X, pady=(0, 5))
        treeview_frame.columnconfigure(0, weight=1)

        tree = ttk.Treeview(treeview_frame, selectmode="browse")
        vsb = ttk.Scrollbar(treeview_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(treeview_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        treeview_frame.rowconfigure(0, weight=1)
        self.widgets["exp_tree"] = tree

        self.exp_manager = ExperimentManager(tree, self.root, self.log)
        self.exp_manager.populate_treeview()
        tree.bind("<<TreeviewSelect>>", self.on_treeview_select)

        tree_button_frame = ttk.Frame(treeview_frame)
        tree_button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        ttk.Button(
            tree_button_frame, text="追加", command=self.exp_manager.add_entry
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            tree_button_frame, text="編集", command=self.exp_manager.edit_entry
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            tree_button_frame, text="削除", command=self.exp_manager.delete_entry
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            tree_button_frame, text="リストを保存", command=self.exp_manager.save_data
        ).pack(side=tk.RIGHT, padx=2)

        param_frame = ttk.LabelFrame(
            settings_outer_frame, text="推論パラメータ", padding=10
        )
        param_frame.pack(fill=tk.X, pady=(5, 5))
        param_frame.columnconfigure(0, weight=1)
        param_frame.columnconfigure(1, weight=3)

        main_settings_frame = ttk.Frame(param_frame)
        main_settings_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_settings_frame.columnconfigure(1, weight=1)
        self._create_main_param_widgets(main_settings_frame)

        exec_mode_frame = ttk.Frame(param_frame)
        exec_mode_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        exec_mode_frame.columnconfigure(1, weight=1)
        self._create_exec_mode_widgets(exec_mode_frame)

        self.widgets["options_toggle_button"] = ttk.Button(
            param_frame,
            text="詳細オプションを表示 ▼",
            command=self.toggle_options_visibility,
            style="Toggle.TButton",
        )
        self.widgets["options_toggle_button"].grid(
            row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0)
        )

        self.options_frame = ttk.Frame(param_frame, padding=(10, 5))
        self.options_frame.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5)
        )
        self._create_options_widgets(self.options_frame)
        self.options_frame.grid_remove()

    def _create_main_param_widgets(self, parent):

        row_idx = 0
        ttk.Label(parent, text="バージョン:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        self.widgets["version_entry"] = ttk.Entry(
            parent, textvariable=self.config_display["version"], state="readonly"
        )
        self.widgets["version_entry"].grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        ttk.Label(parent, text="実験名:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(parent, textvariable=self.config_manual["experiment_name"]).grid(
            row=row_idx, column=1, sticky=tk.EW, pady=2
        )
        row_idx += 1

        ttk.Label(parent, text="パターン番号:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            parent, from_=0, to=100, textvariable=self.config_manual["pattern_num"]
        ).grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        ttk.Label(parent, text="スケール:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        scale_frame = ttk.Frame(parent)
        scale_frame.grid(row=row_idx, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(
            scale_frame, text="2", variable=self.config_manual["scale"], value=2
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            scale_frame, text="4", variable=self.config_manual["scale"], value=4
        ).pack(side=tk.LEFT, padx=5)
        row_idx += 1

    def _create_exec_mode_widgets(self, parent):

        row_idx_exec = 0
        ttk.Label(parent, text="実行モード:").grid(
            row=row_idx_exec, column=0, sticky=tk.W, pady=2
        )
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=row_idx_exec, column=1, sticky=tk.W, pady=2)
        self.widgets["mode_range_rb"] = ttk.Radiobutton(
            mode_frame,
            text="範囲実行",
            variable=self.config_manual["execution_mode"],
            value="range",
        )
        self.widgets["mode_range_rb"].pack(side=tk.LEFT, padx=5)
        self.widgets["mode_single_rb"] = ttk.Radiobutton(
            mode_frame,
            text="単一実行",
            variable=self.config_manual["execution_mode"],
            value="single",
        )
        self.widgets["mode_single_rb"].pack(side=tk.LEFT, padx=5)
        row_idx_exec += 1

        self.widgets["model_save_freq_label"] = ttk.Label(
            parent, text="モデル保存頻度:"
        )
        self.widgets["model_save_freq_label"].grid(
            row=row_idx_exec, column=0, sticky=tk.W, pady=2
        )
        self.widgets["model_save_freq_entry"] = ttk.Entry(
            parent,
            textvariable=self.config_display["model_save_freq"],
            state="readonly",
        )
        self.widgets["model_save_freq_entry"].grid(
            row=row_idx_exec, column=1, sticky=tk.EW, pady=2
        )
        row_idx_exec += 1

        self.widgets["total_iter_label"] = ttk.Label(parent, text="総イテレーション:")
        self.widgets["total_iter_label"].grid(
            row=row_idx_exec, column=0, sticky=tk.W, pady=2
        )
        self.widgets["total_iter_entry"] = ttk.Entry(
            parent, textvariable=self.config_display["total_iter"], state="readonly"
        )
        self.widgets["total_iter_entry"].grid(
            row=row_idx_exec, column=1, sticky=tk.EW, pady=2
        )
        row_idx_exec += 1

        self.widgets["target_iter_label"] = ttk.Label(
            parent, text="ターゲットイテレーション:"
        )
        self.widgets["target_iter_label"].grid(
            row=row_idx_exec, column=0, sticky=tk.W, pady=2
        )
        self.widgets["target_iter_entry"] = ttk.Entry(
            parent, textvariable=self.config_manual["target_iteration"]
        )
        self.widgets["target_iter_entry"].grid(
            row=row_idx_exec, column=1, sticky=tk.EW, pady=2
        )
        row_idx_exec += 1

    def _create_options_widgets(self, parent):

        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=3)

        options_left_frame = ttk.Frame(parent)
        options_left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        options_left_frame.columnconfigure(1, weight=1)
        ttk.Label(options_left_frame, text="モデル名:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(
            options_left_frame, textvariable=self.config_manual["model_name"]
        ).grid(row=0, column=1, sticky=tk.EW, pady=2)

        options_right_frame = ttk.Frame(parent)
        options_right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        options_right_frame.columnconfigure(1, weight=1)
        row_idx_opt = 0
        self.create_path_setting(
            options_right_frame,
            "実験ディレクトリ:",
            "experiments_dir",
            row_idx_opt,
            is_dir=True,
        )
        row_idx_opt += 1
        self.create_path_setting(
            options_right_frame,
            "入力ディレクトリ(ベース):",
            "csv_input_dir",
            row_idx_opt,
            is_dir=True,
        )
        row_idx_opt += 1
        ttk.Label(options_right_frame, text="出力ディレクトリ(ベース名):").grid(
            row=row_idx_opt, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(
            options_right_frame, textvariable=self.config_manual["csv_output_dir"]
        ).grid(row=row_idx_opt, column=1, sticky=tk.EW, pady=2)
        row_idx_opt += 1
        self.create_path_setting(
            options_right_frame,
            "Python実行パス:",
            "python_path",
            row_idx_opt,
            is_dir=False,
        )
        row_idx_opt += 1
        self.create_path_setting(
            options_right_frame,
            "作業ディレクトリ:",
            "working_dir",
            row_idx_opt,
            is_dir=True,
        )
        row_idx_opt += 1

        save_paths_button = ttk.Button(
            options_right_frame, text="現在のパス設定を保存", command=self.save_paths
        )
        save_paths_button.grid(
            row=row_idx_opt, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )

    def save_paths(self):

        paths = {
            "experiments_dir": self.config_manual["experiments_dir"].get(),
            "python_path": self.config_manual["python_path"].get(),
            "working_dir": self.config_manual["working_dir"].get(),
        }
        self.path_config.update_config(paths)

        scale = self.config_manual["scale"].get()
        scale_config = {
            "csv_input_dir": self.config_manual["csv_input_dir"].get(),
            "csv_output_dir": self.config_manual["csv_output_dir"].get(),
        }
        self.path_config.update_scale_config(scale, scale_config)

        self.log("パス設定をファイルに保存しました。")
        messagebox.showinfo("保存完了", "パス設定が保存されました。", parent=self.root)

    def on_treeview_select(self, event):

        selected_data = self.exp_manager.get_selected_data()
        if selected_data:

            self.config_display["version"].set(selected_data.get("version", ""))
            self.config_display["total_iter"].set(selected_data.get("total_iter", 0))
            self.config_display["model_save_freq"].set(
                selected_data.get("model_save_freq", 0)
            )

            best_iter = selected_data.get("best_iter", "")
            try:
                self.config_manual["target_iteration"].set(
                    int(best_iter) if best_iter else 0
                )
            except ValueError:
                self.config_manual["target_iteration"].set(0)

            self.on_scale_change()
        else:

            self.config_display["version"].set("")
            self.config_display["total_iter"].set(0)
            self.config_display["model_save_freq"].set(0)
            self.config_manual["target_iteration"].set(0)
            self.on_scale_change()

    def on_scale_change(self, *args):
        try:
            scale = self.config_manual["scale"].get()

            current_input_dir = self.config_manual["csv_input_dir"].get()
            current_output_dir = self.config_manual["csv_output_dir"].get()

            scale_config = self.path_config.get_scale_config(scale)
            default_input = scale_config.get("csv_input_dir", "")
            default_output = scale_config.get("csv_output_dir", "")

            other_scales = [s for s in [2, 4] if s != scale]
            update_input = not current_input_dir or any(
                current_input_dir
                == self.path_config.get_scale_config(s).get("csv_input_dir")
                for s in other_scales
                if self.path_config.get_scale_config(s).get("csv_input_dir")
            )
            update_output = not current_output_dir or any(
                current_output_dir
                == self.path_config.get_scale_config(s).get("csv_output_dir")
                for s in other_scales
                if self.path_config.get_scale_config(s).get("csv_output_dir")
            )

            if update_input:
                self.config_manual["csv_input_dir"].set(default_input)
            if update_output:
                self.config_manual["csv_output_dir"].set(default_output)

        except tk.TclError:
            pass

    def toggle_options_visibility(self):

        if self.options_visible.get():
            self.options_frame.grid_remove()
            self.widgets["options_toggle_button"].config(text="詳細オプションを表示 ▼")
            self.options_visible.set(False)
        else:
            self.options_frame.grid()
            self.widgets["options_toggle_button"].config(text="詳細オプションを隠す ▲")
            self.options_visible.set(True)

    def create_path_setting(self, parent, label_text, config_key, row, is_dir=True):

        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=2)
        path_frame = ttk.Frame(parent)
        path_frame.grid(row=row, column=1, sticky=tk.EW, pady=2)
        path_frame.columnconfigure(0, weight=1)

        var = self.config_manual.get(config_key)
        if var is None:
            print(f"Warning: Config key '{config_key}' not found in config_manual.")
            var = tk.StringVar()

        entry = ttk.Entry(path_frame, textvariable=var)
        entry.grid(row=0, column=0, sticky=tk.EW)
        self.widgets[f"{config_key}_entry"] = entry

        cmd = (
            (lambda k=config_key: self.browse_directory(k))
            if is_dir
            else (lambda k=config_key: self.browse_file(k))
        )
        button = ttk.Button(path_frame, text="参照", command=cmd)
        button.grid(row=0, column=1, padx=(5, 0))
        self.widgets[f"{config_key}_button"] = button

    def toggle_parameter_state(self, *args):

        mode = self.config_manual["execution_mode"].get()
        is_single_mode = mode == "single"

        target_iter_widgets = [
            self.widgets.get("target_iter_label"),
            self.widgets.get("target_iter_entry"),
        ]
        for widget in target_iter_widgets:
            if widget and widget.winfo_exists():
                widget.config(state=tk.NORMAL if is_single_mode else tk.DISABLED)

    def create_execution_widgets(self, parent_container):

        controls_frame = ttk.Frame(parent_container)
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        ttk.Button(
            controls_frame,
            text="推論実行",
            command=self.run_inference,
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

        output_frame = ttk.LabelFrame(parent_container, text="出力ログ", padding=10)
        output_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=10
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        self.widgets["output_text"] = self.output_text

    def log(self, message):

        output_widget = self.widgets.get("output_text")
        if output_widget and output_widget.winfo_exists():
            output_widget.config(state=tk.NORMAL)
            output_widget.insert(tk.END, str(message) + "\n")
            output_widget.see(tk.END)
            output_widget.config(state=tk.DISABLED)

            self.root.update_idletasks()
        else:

            print(message)

    def browse_directory(self, config_key):

        var = self.config_manual.get(config_key)
        if var is None:
            return
        initial_dir = var.get()

        if not os.path.isdir(initial_dir):
            initial_dir = os.path.dirname(initial_dir)
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        if not os.path.isdir(initial_dir):
            initial_dir = "/"
        directory = filedialog.askdirectory(
            initialdir=initial_dir,
            title=f"{config_key} ディレクトリ選択",
            parent=self.root,
        )
        if directory:
            var.set(directory)

    def browse_file(self, config_key):

        var = self.config_manual.get(config_key)
        if var is None:
            return
        initial_dir = os.path.dirname(var.get())

        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        if not os.path.isdir(initial_dir):
            initial_dir = "/"
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir, title=f"{config_key} ファイル選択", parent=self.root
        )
        if file_path:
            var.set(file_path)

    def run_inference(self):

        try:

            selected_exp_data = self.exp_manager.get_selected_data()
            if not selected_exp_data:
                messagebox.showerror(
                    "設定エラー",
                    "実験設定リストからバージョンを選択してください。",
                    parent=self.root,
                )
                return
            selected_version = selected_exp_data.get("version", "")

            p_manual = {k: v.get() for k, v in self.config_manual.items()}

            validation_errors = self._validate_parameters(p_manual, selected_exp_data)
            if validation_errors:
                messagebox.showerror(
                    "設定エラー",
                    "以下のパラメータを確認してください:\n- "
                    + "\n- ".join(validation_errors),
                    parent=self.root,
                )
                return

            epochs_to_run, log_params, validation_warnings = (
                self._prepare_epochs_to_run(p_manual, selected_exp_data)
            )
            if epochs_to_run is None:
                return
            if validation_warnings:
                if not messagebox.askyesno(
                    "警告",
                    "以下の点を確認してください:\n- "
                    + "\n- ".join(validation_warnings)
                    + "\n\n処理を続行しますか？",
                    icon="warning",
                    parent=self.root,
                ):
                    return

            self._prepare_for_run()
            self._log_initial_settings(selected_version, p_manual, log_params)

            all_success, final_progress = self._execute_inference_loop(
                epochs_to_run, selected_version, p_manual
            )

            self._finalize_run(all_success, p_manual["execution_mode"], final_progress)

        except Exception as e:

            self.log(f"致命的なエラーが発生しました: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror(
                "致命的なエラー",
                f"予期せぬエラーが発生しました:\n{str(e)}\n詳細はログを確認してください。",
                parent=self.root,
            )
            if hasattr(self, "progress_label"):
                self.progress_label.config(text="致命的エラー")

    def _validate_parameters(self, p_manual, selected_exp_data):

        errors = []

        if not (
            isinstance(p_manual["pattern_num"], int) and p_manual["pattern_num"] >= 0
        ):
            errors.append("パターン番号は0以上の整数")
        if not isinstance(p_manual["scale"], int) or p_manual["scale"] not in [2, 4]:
            errors.append("スケールは2または4")
        for k in [
            "experiment_name",
            "model_name",
            "csv_output_dir",
            "csv_input_dir",
            "experiments_dir",
            "python_path",
            "working_dir",
        ]:
            if not p_manual[k]:
                errors.append(f"{k} が未入力")

        paths_to_check = {
            "実験D": (p_manual["experiments_dir"], True),
            "入力D": (p_manual["csv_input_dir"], True),
            "作業D": (p_manual["working_dir"], True),
            "PythonP": (p_manual["python_path"], False),
        }
        for name, (path, is_dir) in paths_to_check.items():
            if path:
                if is_dir and not os.path.isdir(path):
                    errors.append(f"{name} ディレクトリ無し: {path}")
                if not is_dir and not os.path.isfile(path):
                    errors.append(f"{name} ファイル無し: {path}")
        return errors

    def _prepare_epochs_to_run(self, p_manual, selected_exp_data):

        epochs_to_run = []
        log_params = {}
        warnings = []
        ver_total_iter = selected_exp_data.get("total_iter", 0)
        ver_save_freq = selected_exp_data.get("model_save_freq", 0)
        execution_mode = p_manual["execution_mode"]

        if execution_mode == "range":
            if ver_total_iter <= 0 or ver_save_freq <= 0:
                messagebox.showerror(
                    "設定エラー",
                    f"選択バージョンの総Iter({ver_total_iter})または保存頻度({ver_save_freq})が無効です。",
                    parent=self.root,
                )
                return None, {}, []
            epochs_to_run = list(
                range(ver_save_freq, ver_total_iter + 1, ver_save_freq)
            )
            if not epochs_to_run:
                messagebox.showwarning(
                    "情報", "範囲実行の対象エポックがありません。", parent=self.root
                )
                return [], {}, []
            log_params = {
                "保存頻度": ver_save_freq,
                "総Iter": ver_total_iter,
                "対象Epoch": epochs_to_run,
            }
        elif execution_mode == "single":
            try:
                target = p_manual["target_iteration"]
                if not (isinstance(target, int) and target > 0):
                    raise ValueError("ターゲットIterは正整数")

                if target > ver_total_iter:
                    warnings.append(
                        f"ターゲットIter ({target}) > 総Iter ({ver_total_iter})"
                    )
                if ver_save_freq > 0 and target % ver_save_freq != 0:
                    warnings.append(
                        f"ターゲットIter ({target}) は保存頻度 ({ver_save_freq}) の倍数ではない (モデル無いかも)"
                    )
                epochs_to_run = [target]
                log_params = {"ターゲットIter": target}
            except (tk.TclError, ValueError) as e:
                messagebox.showerror(
                    "設定エラー", f"単一実行パラメータ無効:\n{e}", parent=self.root
                )
                return None, {}, []
        else:
            messagebox.showerror("エラー", "無効な実行モード", parent=self.root)
            return None, {}, []

        return epochs_to_run, log_params, warnings

    def _prepare_for_run(self):

        if self.widgets.get("output_text"):
            self.widgets["output_text"].config(state=tk.NORMAL)
            self.widgets["output_text"].delete(1.0, tk.END)
            self.widgets["output_text"].config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.progress_label.config(text="0%")
        self.root.update_idletasks()

    def _log_initial_settings(self, version, p_manual, log_params):

        self.log("=== 推論実行設定 ===")
        self.log(
            f"モード: {'範囲' if p_manual['execution_mode'] == 'range' else '単一'}"
        )
        self.log(f"バージョン: {version}")

        self.log(
            f" (総Iter: {self.config_display['total_iter'].get()}, 保存頻度: {self.config_display['model_save_freq'].get()})"
        )
        for k in ["experiment_name", "pattern_num", "model_name", "scale"]:
            self.log(f"{k}: {p_manual[k]}")
        for k, v in log_params.items():
            self.log(f"{k}: {v}")
        self.log(f"入力D(Base): {p_manual['csv_input_dir']}")
        self.log(f"出力D(Base): {p_manual['csv_output_dir']}")
        self.log(f"実験D: {p_manual['experiments_dir']}")
        self.log(f"PythonP: {p_manual['python_path']}")
        self.log(f"作業D: {p_manual['working_dir']}")
        self.log("\n処理開始...")

    def _execute_inference_loop(self, epochs_to_run, version, p_manual):

        total_epochs = len(epochs_to_run)
        processed_count = 0
        all_success = True
        current_progress = 0

        for epoch in epochs_to_run:
            processed_count += 1
            log_prefix = (
                f"範囲({processed_count}/{total_epochs})"
                if p_manual["execution_mode"] == "range"
                else "単一"
            )
            self.log(f"\n=== {log_prefix}: Epoch {epoch} 開始 ===")
            if p_manual["execution_mode"] == "single":
                self.progress_label.config(text="実行中...")

            success = run_realesrgan_inference(
                p_manual["pattern_num"],
                version,
                epoch,
                p_manual["experiment_name"],
                p_manual["csv_input_dir"],
                p_manual["model_name"],
                p_manual["scale"],
                p_manual["csv_output_dir"],
                p_manual["experiments_dir"],
                p_manual["python_path"],
                p_manual["working_dir"],
                self.log,
                verbose=True,
            )

            current_progress = (processed_count / total_epochs) * 100
            self.progress_var.set(current_progress)
            progress_text = (
                f"{int(current_progress)}%"
                if p_manual["execution_mode"] == "range"
                else ("完了" if success else "エラー")
            )
            self.progress_label.config(text=progress_text)
            self.root.update_idletasks()

            if not success:
                self.log(f"\nエラー: Epoch {epoch} の処理に失敗しました。")
                error_msg = f"Epoch {epoch} 失敗。" + (
                    "\n範囲実行を中断。"
                    if p_manual["execution_mode"] == "range"
                    else ""
                )
                messagebox.showerror("実行エラー", error_msg, parent=self.root)
                all_success = False
                if p_manual["execution_mode"] == "range":
                    break

        return all_success, current_progress

    def _finalize_run(self, all_success, execution_mode, final_progress):

        if all_success:
            self.log("\n全処理 正常完了。")
            messagebox.showinfo(
                "完了", "全ての要求された処理が正常に完了しました。", parent=self.root
            )
            self.progress_var.set(100)
            final_text = "100%" if execution_mode == "range" else "完了"
            self.progress_label.config(text=final_text)
        else:
            self.log("\n処理中にエラーが発生しました。")
            if execution_mode == "range":

                self.progress_label.config(text=f"{int(final_progress)}% (エラー)")
            else:

                self.progress_label.config(text="エラー")


def main():
    root = tk.Tk()
    app = RealESRGANGUI(root)

    def on_closing():
        try:
            if hasattr(app, "exp_manager") and app.exp_manager:
                app.exp_manager.save_data()

            app.save_paths()
        except Exception as e:
            print(f"終了時のデータ保存中にエラー: {e}")
        finally:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
