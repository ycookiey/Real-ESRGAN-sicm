import tkinter as tk
from tkinter import ttk


class ParametersPanel:

    def __init__(self, parent, root, path_config=None):
        self.parent = parent
        self.root = root
        self.path_config = path_config

        self.frame = self._create_parameters_frame()

    def _create_parameters_frame(self):
        params_frame = ttk.LabelFrame(self.parent, text="表示設定", padding=10)
        params_frame.columnconfigure(1, weight=1)

        ttk.Label(params_frame, text="目標サイズ:").grid(
            row=0, column=0, sticky=tk.W, pady=2
        )
        size_frame = ttk.Frame(params_frame)
        size_frame.grid(row=0, column=1, sticky=tk.W, pady=2)

        self.target_width = tk.IntVar(value=256)
        self.target_height = tk.IntVar(value=256)

        ttk.Label(size_frame, text="幅:").pack(side=tk.LEFT)
        ttk.Spinbox(
            size_frame,
            from_=32,
            to=1024,
            increment=32,
            width=5,
            textvariable=self.target_width,
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(size_frame, text="高さ:").pack(side=tk.LEFT)
        ttk.Spinbox(
            size_frame,
            from_=32,
            to=1024,
            increment=32,
            width=5,
            textvariable=self.target_height,
        ).pack(side=tk.LEFT)

        ttk.Label(params_frame, text="表示倍率:").grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        self.scale_factor = tk.DoubleVar(value=1.0)
        ttk.Spinbox(
            params_frame,
            from_=0.5,
            to=4.0,
            increment=0.5,
            width=5,
            textvariable=self.scale_factor,
        ).grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(params_frame, text="出力ディレクトリ:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        # デフォルト出力先を設定
        default_output_dir = self._get_default_output_dir()
        self.output_dir = tk.StringVar(value=default_output_dir)
        output_dir_frame = ttk.Frame(params_frame)
        output_dir_frame.grid(row=2, column=1, sticky=tk.EW, pady=2)
        output_dir_frame.columnconfigure(0, weight=1)

        ttk.Entry(output_dir_frame, textvariable=self.output_dir).grid(
            row=0, column=0, sticky=tk.EW
        )
        ttk.Button(
            output_dir_frame, text="参照", command=lambda: self._browse_directory()
        ).grid(row=0, column=1, padx=(5, 0))

        return params_frame

    def _get_default_output_dir(self):
        """デフォルト出力ディレクトリを取得"""
        import os
        
        if self.path_config:
            working_dir = self.path_config.get_path("working_dir")
            if working_dir and os.path.exists(working_dir):
                return os.path.join(working_dir, "comparison_results")
        
        # path_configが無い場合は現在のディレクトリを使用
        return os.path.join(os.getcwd(), "comparison_results")

    def _browse_directory(self):
        from tkinter import filedialog
        import os

        initial_dir = self.output_dir.get()

        if not os.path.isdir(initial_dir):
            initial_dir = os.path.dirname(initial_dir)
        if not os.path.isdir(initial_dir):
            initial_dir = os.path.expanduser("~")
        if not os.path.isdir(initial_dir):
            initial_dir = "/"

        directory = filedialog.askdirectory(
            initialdir=initial_dir, title="出力ディレクトリ選択", parent=self.root
        )

        if directory:
            self.output_dir.set(directory)
