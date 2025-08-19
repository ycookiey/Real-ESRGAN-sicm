import os
import tkinter as tk
from tkinter import ttk

from image_comparison_folder_selector import FolderSelector
from image_comparison_parameters import ParametersPanel
from image_comparison_preview import PreviewPanel
from image_comparison_runner import ComparisonRunner
from path_config import PathConfig


class ImageComparisonUI:

    def __init__(self, parent, root, log_callback):

        self.parent = parent
        self.root = root
        self.log = log_callback
        self.path_config = PathConfig()

        self._create_widgets()

    def _create_widgets(self):

        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(4, weight=1)

        self.folder_selector = FolderSelector(
            main_frame, self.root, self.log, self.path_config
        )
        self.folder_selector.frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.parameters_panel = ParametersPanel(main_frame, self.root, self.path_config)
        self.parameters_panel.frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.preview_panel = PreviewPanel(main_frame)
        self.preview_panel.frame.grid(
            row=0, column=1, rowspan=5, sticky="nsew", padx=5, pady=5
        )

        self.comparison_runner = ComparisonRunner(
            main_frame,
            self.root,
            self.log,
            self.folder_selector,
            self.parameters_panel,
            self.preview_panel,
        )
        self.comparison_runner.controls_frame.grid(
            row=2, column=0, sticky="nsew", padx=5, pady=5
        )
        self.comparison_runner.log_frame.grid(
            row=3, column=0, sticky="nsew", padx=5, pady=5
        )
