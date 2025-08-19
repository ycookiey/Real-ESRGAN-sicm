import os
import tkinter as tk
from tkinter import ttk, messagebox
import traceback

from inference_runner import run_realesrgan_inference


class InferenceControls:
    def __init__(
        self,
        parent_frame,
        root,
        config_display,
        config_manual,
        exp_manager,
        log_callback,
        path_config,
    ):
        self.parent_frame = parent_frame
        self.root = root
        self.config_display = config_display
        self.config_manual = config_manual
        self.exp_manager = exp_manager
        self.log = log_callback
        self.path_config = path_config

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_label = None

        self._create_control_widgets()

    def _create_control_widgets(self):
        controls_frame = ttk.Frame(self.parent_frame)
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

        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, mode="determinate"
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.progress_label = ttk.Label(progress_frame, text="0%")
        self.progress_label.pack(side=tk.RIGHT)

    def run_inference(self):
        try:
            p_manual = {k: v.get() for k, v in self.config_manual.items()}
            execution_mode = p_manual["execution_mode"]

            if execution_mode == "pretrained":
                self._run_pretrained_inference(p_manual)
            else:

                self._run_experiment_inference(p_manual)

        except Exception as e:
            self.log(f"致命的なエラーが発生しました: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror(
                "致命的なエラー",
                f"予期せぬエラーが発生しました:\n{str(e)}\n詳細はログを確認してください。",
                parent=self.root,
            )
            if self.progress_label:
                self.progress_label.config(text="致命的エラー")

    def _run_pretrained_inference(self, p_manual):
        try:

            validation_errors = self._validate_pretrained_parameters(p_manual)
            if validation_errors:
                messagebox.showerror(
                    "設定エラー",
                    "以下のパラメータを確認してください:\n- "
                    + "\n- ".join(validation_errors),
                    parent=self.root,
                )
                return

            pretrained_model_path = p_manual["pretrained_model_path"]

            self._prepare_for_run()
            self._log_pretrained_settings(p_manual, pretrained_model_path)
            
            self.root.update_idletasks()

            success = run_realesrgan_inference(
                pattern_num=p_manual["pattern_num"],
                version="",
                epoch=0,
                experiment_name="",
                base_input_dir=p_manual["csv_input_dir"],
                model_name=p_manual["model_name"],
                scale=p_manual["scale"],
                base_output_dir=p_manual["csv_output_dir"],
                experiments_dir=p_manual["experiments_dir"],
                python_path=p_manual["python_path"],
                working_dir=p_manual["working_dir"],
                log_callback=self.log,
                verbose=True,
                pretrained_model_path=pretrained_model_path,
            )

            if success:
                self.log("\n事前訓練済みモデル推論 正常完了。")
                self.progress_var.set(100)
                self.progress_label.config(text="完了")
                self.root.update_idletasks()
                messagebox.showinfo(
                    "完了",
                    "事前訓練済みモデルでの推論が正常に完了しました。",
                    parent=self.root,
                )
            else:
                self.log("\n事前訓練済みモデル推論中にエラーが発生しました。")
                self.progress_label.config(text="エラー")
                self.root.update_idletasks()

        except Exception as e:
            self.log(f"事前訓練済みモデル推論エラー: {str(e)}")
            self.log(traceback.format_exc())
            messagebox.showerror(
                "推論エラー",
                f"事前訓練済みモデル推論中にエラーが発生しました:\n{str(e)}",
                parent=self.root,
            )
            if self.progress_label:
                self.progress_label.config(text="エラー")

    def _run_experiment_inference(self, p_manual):

        selected_exp_data = self.exp_manager.get_selected_data()
        if not selected_exp_data:
            messagebox.showerror(
                "設定エラー",
                "実験設定リストからバージョンを選択してください。",
                parent=self.root,
            )
            return

        selected_version = selected_exp_data.get("version", "")

        validation_errors = self._validate_experiment_parameters(
            p_manual, selected_exp_data
        )
        if validation_errors:
            messagebox.showerror(
                "設定エラー",
                "以下のパラメータを確認してください:\n- "
                + "\n- ".join(validation_errors),
                parent=self.root,
            )
            return

        epochs_to_run, log_params, validation_warnings = self._prepare_epochs_to_run(
            p_manual, selected_exp_data
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

    def _validate_pretrained_parameters(self, p_manual):
        errors = []

        if not (
            isinstance(p_manual["pattern_num"], int) and p_manual["pattern_num"] >= 0
        ):
            errors.append("パターン番号は0以上の整数")
        if not isinstance(p_manual["scale"], int) or p_manual["scale"] not in [2, 4]:
            errors.append("スケールは2または4")
        if not p_manual["dataset"]:
            errors.append("データセットが未選択")

        if not p_manual["pretrained_model_path"]:
            errors.append("事前訓練済みモデルパスが未選択")
        elif not os.path.isfile(p_manual["pretrained_model_path"]):
            errors.append(
                f"事前訓練済みモデルファイルが存在しません: {p_manual['pretrained_model_path']}"
            )

        required_fields = [
            "model_name",
            "csv_output_dir",
            "csv_input_dir",
            "python_path",
            "working_dir",
        ]
        for field in required_fields:
            if not p_manual[field]:
                errors.append(f"{field} が未入力")

        paths_to_check = {
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

    def _validate_experiment_parameters(self, p_manual, selected_exp_data):
        errors = []

        if not (
            isinstance(p_manual["pattern_num"], int) and p_manual["pattern_num"] >= 0
        ):
            errors.append("パターン番号は0以上の整数")
        if not isinstance(p_manual["scale"], int) or p_manual["scale"] not in [2, 4]:
            errors.append("スケールは2または4")
        if not p_manual["dataset"]:
            errors.append("データセットが未選択")

        required_fields = [
            "experiment_name",
            "model_name",
            "csv_output_dir",
            "csv_input_dir",
            "experiments_dir",
            "python_path",
            "working_dir",
        ]
        for field in required_fields:
            if not p_manual[field]:
                errors.append(f"{field} が未入力")

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

    def _log_pretrained_settings(self, p_manual, pretrained_model_path):
        self.log("=== 事前訓練済みモデル推論実行設定 ===")
        self.log(f"モード: 事前訓練済み")
        self.log(f"データセット: {p_manual['dataset']}")
        self.log(f"事前訓練済みモデル: {os.path.basename(pretrained_model_path)}")
        self.log(f"モデルパス: {pretrained_model_path}")

        for k in ["pattern_num", "model_name", "scale"]:
            self.log(f"{k}: {p_manual[k]}")

        self.log(f"入力D(Base): {p_manual['csv_input_dir']}")
        self.log(f"出力D(Base): {p_manual['csv_output_dir']}")
        self.log(f"PythonP: {p_manual['python_path']}")
        self.log(f"作業D: {p_manual['working_dir']}")
        self.log("\n処理開始...")

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
        self.progress_var.set(0)
        self.progress_label.config(text="実行中...")
        self.root.update_idletasks()

    def _log_initial_settings(self, version, p_manual, log_params):
        self.log("=== 実験モデル推論実行設定 ===")
        self.log(
            f"モード: {'範囲' if p_manual['execution_mode'] == 'range' else '単一'}"
        )
        self.log(f"データセット: {p_manual['dataset']}")
        self.log(f"バージョン: {version}")
        self.log(
            f" (総Iter: {self.config_display['total_iter'].get()}, "
            f"保存頻度: {self.config_display['model_save_freq'].get()})"
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
            
            self.root.update_idletasks()

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
                pretrained_model_path=None,
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
            self.progress_var.set(100)
            final_text = "100%" if execution_mode == "range" else "完了"
            self.progress_label.config(text=final_text)
            self.root.update_idletasks()
            messagebox.showinfo(
                "完了", "全ての要求された処理が正常に完了しました。", parent=self.root
            )
        else:
            self.log("\n処理中にエラーが発生しました。")
            if execution_mode == "range":
                self.progress_label.config(text=f"{int(final_progress)}% (エラー)")
            else:
                self.progress_label.config(text="エラー")
            self.root.update_idletasks()
