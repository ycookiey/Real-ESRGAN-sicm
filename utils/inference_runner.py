import os
import subprocess
from pathlib import Path
import traceback
from typing import Callable


def run_realesrgan_inference(
    pattern_num: int,
    version: str,
    epoch: int,
    experiment_name: str,
    base_input_dir: str,
    model_name: str,
    scale: int,
    base_output_dir: str,
    experiments_dir: str,
    python_path: str,
    working_dir: str,
    log_callback: Callable[[str], None],
    verbose: bool = True,
) -> bool:

    log = log_callback
    try:

        base_input_dir_abs = os.path.abspath(base_input_dir)

        output_dir_rel = os.path.normpath(
            os.path.join(base_output_dir, version, f"pattern_{pattern_num}", str(epoch))
        )
        working_dir_abs = os.path.abspath(working_dir)
        output_dir_abs = os.path.abspath(os.path.join(working_dir_abs, output_dir_rel))

        experiments_dir_abs = os.path.abspath(experiments_dir)
        python_path_abs = os.path.abspath(python_path)

        input_dir = os.path.normpath(
            os.path.join(base_input_dir_abs, f"lr_test_{pattern_num}")
        )
        model_path = os.path.normpath(
            os.path.join(
                experiments_dir_abs, experiment_name, "models", f"net_g_{epoch}.pth"
            )
        )

        script_path = os.path.join(working_dir_abs, "inference_realesrgan.py")

        script_rel_path = os.path.relpath(script_path, working_dir_abs)

        if not os.path.exists(input_dir):
            log(f"エラー: 入力ディレクトリが存在しません: {input_dir}")
            return False
        if not os.path.exists(model_path):
            log(f"エラー: モデルファイルが存在しません: {model_path}")
            return False
        if not os.path.exists(script_path):
            log(f"エラー: 推論スクリプトが存在しません: {script_path}")
            return False

        Path(output_dir_abs).mkdir(parents=True, exist_ok=True)

        command = [
            python_path_abs,
            script_rel_path,
            "-n",
            model_name,
            "-i",
            os.path.relpath(input_dir, working_dir_abs),
            "--suffix",
            f"realesrgan_pattern_{pattern_num}_ep{epoch}",
            "--outscale",
            str(scale),
            "-o",
            output_dir_rel,
            "--model_path",
            os.path.relpath(model_path, working_dir_abs),
        ]

        if verbose:
            log(f"\n--- 推論実行: Pattern={pattern_num}, Epoch={epoch} ---")
            log(f"作業ディレクトリ(cwd): {working_dir_abs}")

            quoted_command_str = " ".join(
                [f'"{arg}"' if " " in arg else arg for arg in command]
            )
            log(f"実行コマンド: {quoted_command_str}")
            log(f"入力(絶対): {input_dir}")
            log(f"出力(絶対): {output_dir_abs}")
            log(f"モデル(絶対): {model_path}")
            log("--------------------------------------------------")

        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            cwd=working_dir_abs,
            encoding="utf-8",
            errors="replace",
            env=os.environ.copy(),
        )

        log(f"成功: Pattern={pattern_num}, Epoch={epoch} の推論完了。")
        log(f"出力先: {output_dir_abs}")
        if verbose and result.stdout:
            log("--- 標準出力 ---")
            log(result.stdout.strip())
            log("-----------------")
        return True

    except subprocess.CalledProcessError as e:
        log(
            f"エラー: Pattern={pattern_num}, Epoch={epoch} でコマンド実行失敗。終了コード: {e.returncode}"
        )
        quoted_command_err_str = " ".join(
            [f'"{arg}"' if " " in arg else arg for arg in command]
        )
        log(f"失敗したコマンド: {quoted_command_err_str}")
        if e.stdout:
            log("--- 標準出力 ---")
            log(e.stdout.strip())
            log("-----------------")
        if e.stderr:
            log("--- 標準エラー出力 ---")
            log(e.stderr.strip())
            log("--------------------")
        return False
    except FileNotFoundError:

        log(f"エラー: Python実行ファイルまたは推論スクリプトが見つかりません。")
        log(f"Python Path: {python_path_abs}")
        log(f"Script Path: {script_path}")
        return False
    except OSError as e:

        log(
            f"エラー: ファイル/ディレクトリ操作中にOSエラーが発生しました (Pattern={pattern_num}, Epoch={epoch}): {e}"
        )
        return False
    except Exception as e:

        log(
            f"予期せぬエラーが発生しました (Pattern={pattern_num}, Epoch={epoch}): {str(e)}"
        )
        log(traceback.format_exc())
        return False
