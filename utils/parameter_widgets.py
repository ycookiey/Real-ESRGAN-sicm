import os
import tkinter as tk
from tkinter import ttk, filedialog


class ParameterWidgets:
    def __init__(
        self,
        parent_frame,
        config_display,
        config_manual,
        widgets,
        options_visible,
        path_config,
        root,
    ):
        self.parent_frame = parent_frame
        self.config_display = config_display
        self.config_manual = config_manual
        self.widgets = widgets
        self.options_visible = options_visible
        self.path_config = path_config
        self.root = root

        self._create_main_parameters()
        self._create_execution_mode_widgets()
        self._create_options_section()

    def _create_main_parameters(self):
        main_settings_frame = ttk.Frame(self.parent_frame)
        main_settings_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_settings_frame.columnconfigure(1, weight=1)

        row_idx = 0

        ttk.Label(main_settings_frame, text="データセット:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        dataset_combo = ttk.Combobox(
            main_settings_frame,
            textvariable=self.config_manual["dataset"],
            values=self.path_config.get_available_datasets(),
            state="readonly",
        )
        dataset_combo.grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        self.widgets["dataset_combo"] = dataset_combo
        row_idx += 1

        ttk.Label(main_settings_frame, text="バージョン:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        self.widgets["version_entry"] = ttk.Entry(
            main_settings_frame,
            textvariable=self.config_display["version"],
            state="readonly",
        )
        self.widgets["version_entry"].grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        ttk.Label(main_settings_frame, text="実験名:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(
            main_settings_frame, textvariable=self.config_manual["experiment_name"]
        ).grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        ttk.Label(main_settings_frame, text="パターン番号:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        ttk.Spinbox(
            main_settings_frame,
            from_=0,
            to=100,
            textvariable=self.config_manual["pattern_num"],
        ).grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        ttk.Label(main_settings_frame, text="スケール:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        scale_frame = ttk.Frame(main_settings_frame)
        scale_frame.grid(row=row_idx, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(
            scale_frame, text="2", variable=self.config_manual["scale"], value=2
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            scale_frame, text="4", variable=self.config_manual["scale"], value=4
        ).pack(side=tk.LEFT, padx=5)

    def _create_execution_mode_widgets(self):
        exec_mode_frame = ttk.Frame(self.parent_frame)
        exec_mode_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        exec_mode_frame.columnconfigure(1, weight=1)

        row_idx = 0

        ttk.Label(exec_mode_frame, text="実行モード:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        mode_frame = ttk.Frame(exec_mode_frame)
        mode_frame.grid(row=row_idx, column=1, sticky=tk.W, pady=2)

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
        row_idx += 1

        self.widgets["model_save_freq_label"] = ttk.Label(
            exec_mode_frame, text="モデル保存頻度:"
        )
        self.widgets["model_save_freq_label"].grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )

        self.widgets["model_save_freq_entry"] = ttk.Entry(
            exec_mode_frame,
            textvariable=self.config_display["model_save_freq"],
            state="readonly",
        )
        self.widgets["model_save_freq_entry"].grid(
            row=row_idx, column=1, sticky=tk.EW, pady=2
        )
        row_idx += 1

        self.widgets["total_iter_label"] = ttk.Label(
            exec_mode_frame, text="総イテレーション:"
        )
        self.widgets["total_iter_label"].grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )

        self.widgets["total_iter_entry"] = ttk.Entry(
            exec_mode_frame,
            textvariable=self.config_display["total_iter"],
            state="readonly",
        )
        self.widgets["total_iter_entry"].grid(
            row=row_idx, column=1, sticky=tk.EW, pady=2
        )
        row_idx += 1

        self.widgets["target_iter_label"] = ttk.Label(
            exec_mode_frame, text="ターゲットイテレーション:"
        )
        self.widgets["target_iter_label"].grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )

        self.widgets["target_iter_entry"] = ttk.Entry(
            exec_mode_frame, textvariable=self.config_manual["target_iteration"]
        )
        self.widgets["target_iter_entry"].grid(
            row=row_idx, column=1, sticky=tk.EW, pady=2
        )

    def _create_options_section(self):

        self.widgets["options_toggle_button"] = ttk.Button(
            self.parent_frame,
            text="詳細オプションを表示 ▼",
            command=self.toggle_options_visibility,
            style="Toggle.TButton",
        )
        self.widgets["options_toggle_button"].grid(
            row=1, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0)
        )

        self.options_frame = ttk.Frame(self.parent_frame, padding=(10, 5))
        self.options_frame.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5)
        )
        self._create_options_widgets()

    def _create_options_widgets(self):
        self.options_frame.columnconfigure(0, weight=1)
        self.options_frame.columnconfigure(1, weight=3)

        options_left_frame = ttk.Frame(self.options_frame)
        options_left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        options_left_frame.columnconfigure(1, weight=1)

        ttk.Label(options_left_frame, text="モデル名:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(
            options_left_frame, textvariable=self.config_manual["model_name"]
        ).grid(row=0, column=1, sticky=tk.EW, pady=2)

        options_right_frame = ttk.Frame(self.options_frame)
        options_right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        options_right_frame.columnconfigure(1, weight=1)

        row_idx = 0
        path_settings = [
            ("実験ディレクトリ:", "experiments_dir", True),
            ("入力ディレクトリ(ベース):", "csv_input_dir", True),
            ("Python実行パス:", "python_path", False),
            ("作業ディレクトリ:", "working_dir", True),
        ]

        for label_text, config_key, is_dir in path_settings:
            self._create_path_setting(
                options_right_frame, label_text, config_key, row_idx, is_dir
            )
            row_idx += 1

        ttk.Label(options_right_frame, text="出力ディレクトリ(ベース名):").grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )
        ttk.Entry(
            options_right_frame, textvariable=self.config_manual["csv_output_dir"]
        ).grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        row_idx += 1

        save_paths_button = ttk.Button(
            options_right_frame,
            text="現在のパス設定を保存",
            command=self._save_paths_callback,
        )
        save_paths_button.grid(
            row=row_idx, column=0, columnspan=2, sticky="e", pady=(10, 0)
        )

    def _create_path_setting(self, parent, label_text, config_key, row, is_dir=True):
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
            (lambda k=config_key: self._browse_directory(k))
            if is_dir
            else (lambda k=config_key: self._browse_file(k))
        )
        button = ttk.Button(path_frame, text="参照", command=cmd)
        button.grid(row=0, column=1, padx=(5, 0))
        self.widgets[f"{config_key}_button"] = button

    def _browse_directory(self, config_key):
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

    def _browse_file(self, config_key):
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

    def toggle_options_visibility(self):
        if self.options_visible.get():
            self.options_frame.grid_remove()
            self.widgets["options_toggle_button"].config(text="詳細オプションを表示 ▼")
            self.options_visible.set(False)
        else:
            self.options_frame.grid()
            self.widgets["options_toggle_button"].config(text="詳細オプションを隠す ▲")
            self.options_visible.set(True)

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

    def _save_paths_callback(self):

        if hasattr(self, "save_paths_func"):
            self.save_paths_func()

    def set_save_paths_callback(self, callback):
        self.save_paths_func = callback
