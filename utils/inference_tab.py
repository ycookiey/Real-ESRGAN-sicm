import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import traceback

from experiment_manager import ExperimentManager
from inference_controls import InferenceControls
from parameter_widgets import ParameterWidgets


class InferenceTab:
    def __init__(self, parent_frame, root, path_config, log_callback):
        self.parent_frame = parent_frame
        self.root = root
        self.path_config = path_config
        self.main_log = log_callback

        self.config_display = {
            "version": tk.StringVar(),
            "total_iter": tk.IntVar(),
            "model_save_freq": tk.IntVar(),
        }

        self.config_manual = {
            "experiment_name": tk.StringVar(value="finetune_csv_x4_3.1.2"),
            "pattern_num": tk.IntVar(value=0),
            "model_name": tk.StringVar(value="RealESRGAN_x4plus"),
            "dataset": tk.StringVar(value=self.path_config.get_selected_dataset()),
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

        self._create_widgets()
        self._setup_bindings()
        self._initialize_display()

    def _create_widgets(self):

        settings_container = ttk.Frame(self.parent_frame, padding=5)
        settings_container.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))

        execution_container = ttk.Frame(self.parent_frame, padding=5)
        execution_container.pack(
            side=tk.BOTTOM, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5)
        )

        self._create_settings_area(settings_container)

        self._create_execution_area(execution_container)

    def _create_settings_area(self, parent):
        settings_outer_frame = ttk.Frame(parent)
        settings_outer_frame.pack(fill=tk.X, expand=False)

        self._create_experiment_list(settings_outer_frame)

        self._create_parameter_section(settings_outer_frame)

    def _create_experiment_list(self, parent):
        treeview_frame = ttk.LabelFrame(parent, text="実験設定リスト", padding=5)
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

        tree_button_frame = ttk.Frame(treeview_frame)
        tree_button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        buttons = [
            ("追加", self.exp_manager.add_entry),
            ("編集", self.exp_manager.edit_entry),
            ("削除", self.exp_manager.delete_entry),
            ("リストを保存", self.exp_manager.save_data),
        ]

        for i, (text, command) in enumerate(buttons[:-1]):
            ttk.Button(tree_button_frame, text=text, command=command).pack(
                side=tk.LEFT, padx=2
            )
        ttk.Button(tree_button_frame, text=buttons[-1][0], command=buttons[-1][1]).pack(
            side=tk.RIGHT, padx=2
        )

    def _create_parameter_section(self, parent):
        param_frame = ttk.LabelFrame(parent, text="推論パラメータ", padding=10)
        param_frame.pack(fill=tk.X, pady=(5, 5))
        param_frame.columnconfigure(0, weight=1)
        param_frame.columnconfigure(1, weight=3)

        self.parameter_widgets = ParameterWidgets(
            param_frame,
            self.config_display,
            self.config_manual,
            self.widgets,
            self.options_visible,
            self.path_config,
            self.root,
        )

        self.parameter_widgets.set_save_paths_callback(self.save_paths)

    def _create_execution_area(self, parent):

        self.inference_controls = InferenceControls(
            parent,
            self.root,
            self.config_display,
            self.config_manual,
            self.exp_manager,
            self.log,
            self.path_config,
        )

        output_frame = ttk.LabelFrame(parent, text="出力ログ", padding=10)
        output_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=10
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_text.config(state=tk.DISABLED)
        self.widgets["output_text"] = self.output_text

    def _setup_bindings(self):

        self.widgets["exp_tree"].bind("<<TreeviewSelect>>", self.on_treeview_select)

        self.config_manual["dataset"].trace_add("write", self.on_dataset_change)
        self.config_manual["scale"].trace_add("write", self.on_scale_change)
        self.config_manual["execution_mode"].trace_add(
            "write", self.parameter_widgets.toggle_parameter_state
        )

    def _initialize_display(self):
        self.on_dataset_change()
        self.parameter_widgets.toggle_parameter_state()

        first_item_iid = self.exp_manager.select_first_item()
        if first_item_iid:
            self.on_treeview_select(None)

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

            self.on_dataset_change()
        else:
            self.config_display["version"].set("")
            self.config_display["total_iter"].set(0)
            self.config_display["model_save_freq"].set(0)
            self.config_manual["target_iteration"].set(0)
            self.on_dataset_change()

    def on_dataset_change(self, *args):
        try:
            current_dataset = self.config_manual["dataset"].get()
            self.path_config.set_selected_dataset(current_dataset)
            self.on_scale_change()
            self.log(f"データセットを '{current_dataset}' に変更しました")
        except tk.TclError:
            pass

    def on_scale_change(self, *args):
        try:
            current_dataset = self.config_manual["dataset"].get()
            scale = self.config_manual["scale"].get()

            current_input_dir = self.config_manual["csv_input_dir"].get()
            current_output_dir = self.config_manual["csv_output_dir"].get()

            scale_config = self.path_config.get_scale_config(scale, current_dataset)
            default_input = scale_config.get("csv_input_dir", "")
            default_output = scale_config.get("csv_output_dir", "")

            datasets = self.path_config.get_available_datasets()
            scales = [2, 4]

            update_input = not current_input_dir
            update_output = not current_output_dir

            if not update_input or not update_output:
                for ds in datasets:
                    for sc in scales:
                        if ds == current_dataset and sc == scale:
                            continue
                        other_config = self.path_config.get_scale_config(sc, ds)
                        if not update_input and current_input_dir == other_config.get(
                            "csv_input_dir", ""
                        ):
                            update_input = True
                        if (
                            not update_output
                            and current_output_dir
                            == other_config.get("csv_output_dir", "")
                        ):
                            update_output = True

            if update_input:
                self.config_manual["csv_input_dir"].set(default_input)
            if update_output:
                self.config_manual["csv_output_dir"].set(default_output)

        except tk.TclError:
            pass

    def save_paths(self):
        paths = {
            "experiments_dir": self.config_manual["experiments_dir"].get(),
            "python_path": self.config_manual["python_path"].get(),
            "working_dir": self.config_manual["working_dir"].get(),
        }
        self.path_config.update_config(paths)

        current_dataset = self.config_manual["dataset"].get()
        self.path_config.set_selected_dataset(current_dataset)

        scale = self.config_manual["scale"].get()
        scale_config = {
            "csv_input_dir": self.config_manual["csv_input_dir"].get(),
            "csv_output_dir": self.config_manual["csv_output_dir"].get(),
        }
        self.path_config.update_scale_config(scale, scale_config, current_dataset)

        self.log("パス設定をファイルに保存しました。")
        messagebox.showinfo("保存完了", "パス設定が保存されました。", parent=self.root)

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
