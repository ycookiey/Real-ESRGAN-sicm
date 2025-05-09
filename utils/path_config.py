import json
import os
import sys
from typing import Dict, Any


class PathConfig:

    def __init__(self, config_file="path_config.json"):
        self.config_file = config_file

        self.default_config = {
            "experiments_dir": "",
            "csv_input_dir": "",
            "csv_output_dir": "",
            "python_path": "",
            "working_dir": "",
            "scale_configs": {
                "2": {
                    "csv_input_dir": "",
                    "csv_output_dir": "x2csvcsv_128_finetuned",
                },
                "4": {
                    "csv_input_dir": "",
                    "csv_output_dir": "x4csvcsv_128_finetuned",
                },
            },
        }
        self.config = self.load_config()

        if not self.config["python_path"] or not self.config["working_dir"]:
            suggested = self.suggest_defaults()
            for key, value in suggested.items():
                if not self.config[key] and value:
                    self.config[key] = value
            self.save_config(self.config)

    def load_config(self) -> Dict[str, Any]:

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                result = self.default_config.copy()
                self._deep_update(result, config)
                return result
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def _deep_update(self, target, source):

        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(target[key], value)
            else:
                target[key] = value

    def save_config(self, config: Dict[str, Any]) -> bool:

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
            return False

    def get_path(self, key: str) -> str:

        return self.config.get(key, self.default_config.get(key, ""))

    def get_scale_config(self, scale: int) -> Dict[str, str]:

        scale_str = str(scale)
        scale_configs = self.config.get("scale_configs", {})
        if scale_str in scale_configs:
            return scale_configs[scale_str]
        return self.default_config.get("scale_configs", {}).get(scale_str, {})

    def update_config(self, config: Dict[str, Any]) -> bool:

        for key, value in config.items():
            if key != "scale_configs":
                self.config[key] = value
        return self.save_config(self.config)

    def update_scale_config(self, scale: int, config: Dict[str, str]) -> bool:

        scale_str = str(scale)
        if "scale_configs" not in self.config:
            self.config["scale_configs"] = {}
        if scale_str not in self.config["scale_configs"]:
            self.config["scale_configs"][scale_str] = {}
        self.config["scale_configs"][scale_str].update(config)
        return self.save_config(self.config)

    def suggest_defaults(self) -> Dict[str, Any]:

        config = self.default_config.copy()

        if not config["python_path"]:
            config["python_path"] = sys.executable

        if not config["working_dir"]:
            config["working_dir"] = os.getcwd()

        if not config["experiments_dir"]:
            experiments_dir = os.path.join(os.getcwd(), "experiments")
            if os.path.exists(experiments_dir):
                config["experiments_dir"] = experiments_dir

        for scale in ["2", "4"]:
            if (
                scale in config["scale_configs"]
                and not config["scale_configs"][scale]["csv_input_dir"]
            ):
                data_dir = os.path.join(os.getcwd(), "dataset")
                if os.path.exists(data_dir):
                    down_sampled_dir = f"0.{'50' if scale == '2' else '25'}down_sampled"
                    config["scale_configs"][scale]["csv_input_dir"] = os.path.join(
                        data_dir, down_sampled_dir
                    )

        return config
