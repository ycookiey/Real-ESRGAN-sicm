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
        self.widgets["experiment_name_entry"] = ttk.Entry(
            main_settings_frame, textvariable=self.config_manual["experiment_name"]
        )
        self.widgets["experiment_name_entry"].grid(
            row=row_idx, column=1, sticky=tk.EW, pady=2
        )
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

        self.widgets["mode_pretrained_rb"] = ttk.Radiobutton(
            mode_frame,
            text="事前訓練済み",
            variable=self.config_manual["execution_mode"],
            value="pretrained",
        )
        self.widgets["mode_pretrained_rb"].pack(side=tk.LEFT, padx=5)
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
        row_idx += 1

        self.widgets["pretrained_model_label"] = ttk.Label(
            exec_mode_frame, text="事前訓練済みモデル:"
        )
        self.widgets["pretrained_model_label"].grid(
            row=row_idx, column=0, sticky=tk.W, pady=2
        )

        pretrained_frame = ttk.Frame(exec_mode_frame)
        pretrained_frame.grid(row=row_idx, column=1, sticky=tk.EW, pady=2)
        pretrained_frame.columnconfigure(0, weight=1)

        self.widgets["pretrained_model_entry"] = ttk.Entry(
            pretrained_frame, textvariable=self.config_manual["pretrained_model_path"]
        )
        self.widgets["pretrained_model_entry"].grid(row=0, column=0, sticky=tk.EW)

        self.widgets["pretrained_model_button"] = ttk.Button(
            pretrained_frame, text="参照", command=self._browse_pretrained_model
        )
        self.widgets["pretrained_model_button"].grid(row=0, column=1, padx=(5, 0))
        row_idx += 1

        self.widgets["pretrained_help_label"] = ttk.Label(
            exec_mode_frame,
            text="推奨: experiments/pretrained_models/RealESRGAN_x[scale]plus.pth",
            font=("Helvetica", 8),
            foreground="gray",
        )
        self.widgets["pretrained_help_label"].grid(
            row=row_idx, column=1, sticky=tk.W, pady=(0, 5)
        )

    def _browse_pretrained_model(self):
        current_path = self.config_manual["pretrained_model_path"].get()

        if current_path and os.path.isfile(current_path):
            initial_dir = os.path.dirname(current_path)
        else:

            experiments_dir = self.config_manual.get(
                "experiments_dir", tk.StringVar()
            ).get()
            if experiments_dir:
                pretrained_dir = os.path.join(experiments_dir, "pretrained_models")
                if os.path.isdir(pretrained_dir):
                    initial_dir = pretrained_dir
                else:
                    initial_dir = experiments_dir
            else:
                initial_dir = os.path.expanduser("~")

        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="事前訓練済みモデル選択",
            filetypes=[("PyTorch Models", "*.pth"), ("All Files", "*.*")],
            parent=self.root,
        )

        if file_path:
            self.config_manual["pretrained_model_path"].set(file_path)

            basename = os.path.basename(file_path).lower()
            if "x2" in basename:
                self.config_manual["scale"].set(2)
            elif "x4" in basename:
                self.config_manual["scale"].set(4)

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
        is_pretrained_mode = mode == "pretrained"
        is_experiment_mode = mode in ["range", "single"]

        experiment_widgets = [
            ("model_save_freq_label", "model_save_freq_entry"),
            ("total_iter_label", "total_iter_entry"),
        ]

        for label_key, entry_key in experiment_widgets:
            for widget_key in [label_key, entry_key]:
                widget = self.widgets.get(widget_key)
                if widget and widget.winfo_exists():
                    if is_experiment_mode:
                        widget.grid()
                        widget.config(
                            state=(
                                tk.NORMAL if entry_key.endswith("_entry") else "normal"
                            )
                        )
                    else:
                        widget.grid_remove()

        target_iter_widgets = [
            self.widgets.get("target_iter_label"),
            self.widgets.get("target_iter_entry"),
        ]
        for widget in target_iter_widgets:
            if widget and widget.winfo_exists():
                if is_single_mode:
                    widget.grid()
                    widget.config(state=tk.NORMAL)
                else:
                    widget.grid_remove()

        pretrained_widgets = [
            self.widgets.get("pretrained_model_label"),
            self.widgets.get("pretrained_model_entry"),
            self.widgets.get("pretrained_model_button"),
            self.widgets.get("pretrained_help_label"),
        ]
        for widget in pretrained_widgets:
            if widget and widget.winfo_exists():
                if is_pretrained_mode:
                    widget.grid()
                    if hasattr(widget, "config"):
                        widget.config(state=tk.NORMAL)
                else:
                    widget.grid_remove()

        experiment_name_entry = self.widgets.get("experiment_name_entry")
        if experiment_name_entry and experiment_name_entry.winfo_exists():
            if is_pretrained_mode:
                experiment_name_entry.config(state=tk.DISABLED)
            else:
                experiment_name_entry.config(state=tk.NORMAL)

    def _save_paths_callback(self):
        if hasattr(self, "save_paths_func"):
            self.save_paths_func()

    def set_save_paths_callback(self, callback):
        self.save_paths_func = callback
