import json
import os
import sys
from typing import Dict, Any, List


class PathConfig:

    def __init__(self, config_file="path_config.json"):
        self.config_file = config_file

        self.default_config = {
            "experiments_dir": "",
            "csv_input_dir": "",
            "csv_output_dir": "",
            "python_path": "",
            "working_dir": "",
            "selected_dataset": "64x64",
            "dataset_configs": {
                "64x64": {
                    "scale_configs": {
                        "2": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x2csvcsv_128_finetuned",
                        },
                        "4": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x4csvcsv_128_finetuned",
                        },
                    }
                },
                "256x256": {
                    "scale_configs": {
                        "2": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x2csvcsv_256_finetuned",
                        },
                        "4": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x4csvcsv_256_finetuned",
                        },
                    }
                },
            },
            "custom_folder_history": [],
            "image_comparison": {
                "include_type_settings": {
                    "lr": True,
                    "bicubic": True,
                    "hr": True,
                },
                "scale_configs": {
                    "2": {
                        "lr_dir": "",
                        "bicubic_dir": "",
                        "hr_dir": "",
                    },
                    "4": {
                        "lr_dir": "",
                        "bicubic_dir": "",
                        "hr_dir": "",
                    },
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

                config = self._migrate_config(config)

                result = self.default_config.copy()
                self._deep_update(result, config)
                return result
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def _migrate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:

        if "dataset_configs" in config:

            if "image_comparison" not in config:
                config["image_comparison"] = self.default_config[
                    "image_comparison"
                ].copy()
            return config

        if "scale_configs" in config:
            print("設定を新しいデータセット構造に移行しています...")

            old_scale_configs = config.pop("scale_configs")

            config["dataset_configs"] = {
                "64x64": {"scale_configs": old_scale_configs},
                "256x256": {
                    "scale_configs": {
                        "2": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x2csvcsv_256_finetuned",
                        },
                        "4": {
                            "csv_input_dir": "",
                            "csv_output_dir": "x4csvcsv_256_finetuned",
                        },
                    }
                },
            }

            config["selected_dataset"] = "64x64"

            config["image_comparison"] = self.default_config["image_comparison"].copy()

            print("移行完了: 既存設定を64x64データセットとして保存しました")

        return config

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

            existing_history = []
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, "r", encoding="utf-8") as f:
                        existing_config = json.load(f)
                        if "custom_folder_history" in existing_config:
                            existing_history = existing_config.get(
                                "custom_folder_history", []
                            )
                except Exception:
                    pass

            if (
                "custom_folder_history" not in config
                or not config["custom_folder_history"]
            ):
                config["custom_folder_history"] = existing_history

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
            import traceback

            traceback.print_exc()
            return False

    def get_path(self, key: str) -> str:
        return self.config.get(key, self.default_config.get(key, ""))

    def get_selected_dataset(self) -> str:
        return self.config.get("selected_dataset", "64x64")

    def set_selected_dataset(self, dataset: str) -> bool:
        if dataset in self.get_available_datasets():
            self.config["selected_dataset"] = dataset
            return self.save_config(self.config)
        return False

    def get_available_datasets(self) -> List[str]:
        dataset_configs = self.config.get("dataset_configs", {})
        return list(dataset_configs.keys())

    def get_scale_config(self, scale: int, dataset: str = None) -> Dict[str, str]:
        if dataset is None:
            dataset = self.get_selected_dataset()

        scale_str = str(scale)
        dataset_configs = self.config.get("dataset_configs", {})

        if dataset in dataset_configs:
            scale_configs = dataset_configs[dataset].get("scale_configs", {})
            if scale_str in scale_configs:
                return scale_configs[scale_str]

        default_dataset_configs = self.default_config.get("dataset_configs", {})
        if dataset in default_dataset_configs:
            default_scale_configs = default_dataset_configs[dataset].get(
                "scale_configs", {}
            )
            return default_scale_configs.get(scale_str, {})

        return {}

    def update_config(self, config: Dict[str, Any]) -> bool:
        for key, value in config.items():
            if key not in ["dataset_configs", "selected_dataset", "image_comparison"]:
                self.config[key] = value
        return self.save_config(self.config)

    def update_scale_config(
        self, scale: int, config: Dict[str, str], dataset: str = None
    ) -> bool:
        if dataset is None:
            dataset = self.get_selected_dataset()

        scale_str = str(scale)

        if "dataset_configs" not in self.config:
            self.config["dataset_configs"] = {}
        if dataset not in self.config["dataset_configs"]:
            self.config["dataset_configs"][dataset] = {"scale_configs": {}}
        if "scale_configs" not in self.config["dataset_configs"][dataset]:
            self.config["dataset_configs"][dataset]["scale_configs"] = {}
        if scale_str not in self.config["dataset_configs"][dataset]["scale_configs"]:
            self.config["dataset_configs"][dataset]["scale_configs"][scale_str] = {}

        self.config["dataset_configs"][dataset]["scale_configs"][scale_str].update(
            config
        )
        return self.save_config(self.config)

    def get_image_comparison_include_settings(self) -> Dict[str, bool]:
        image_comparison = self.config.get("image_comparison", {})
        include_settings = image_comparison.get("include_type_settings", {})

        default_settings = self.default_config["image_comparison"][
            "include_type_settings"
        ]
        result = default_settings.copy()
        result.update(include_settings)

        return result

    def update_image_comparison_include_settings(self, settings: Dict[str, bool]) -> bool:
        if "image_comparison" not in self.config:
            self.config["image_comparison"] = self.default_config[
                "image_comparison"
            ].copy()

        self.config["image_comparison"]["include_type_settings"].update(settings)
        return self.save_config(self.config)

    def get_image_comparison_scale_config(self, scale: int) -> Dict[str, str]:
        scale_str = str(scale)
        image_comparison = self.config.get("image_comparison", {})
        scale_configs = image_comparison.get("scale_configs", {})

        if scale_str in scale_configs:
            return scale_configs[scale_str].copy()

        default_configs = self.default_config["image_comparison"]["scale_configs"]
        return default_configs.get(scale_str, {}).copy()

    def update_image_comparison_scale_config(
        self, scale: int, config: Dict[str, str]
    ) -> bool:
        scale_str = str(scale)

        if "image_comparison" not in self.config:
            self.config["image_comparison"] = self.default_config[
                "image_comparison"
            ].copy()

        if "scale_configs" not in self.config["image_comparison"]:
            self.config["image_comparison"]["scale_configs"] = {}

        if scale_str not in self.config["image_comparison"]["scale_configs"]:
            self.config["image_comparison"]["scale_configs"][scale_str] = {}

        self.config["image_comparison"]["scale_configs"][scale_str].update(config)
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

        for dataset in ["64x64", "256x256"]:
            for scale in ["2", "4"]:
                dataset_config = config["dataset_configs"][dataset]["scale_configs"][
                    scale
                ]
                if not dataset_config.get("csv_input_dir"):
                    data_dir = os.path.join(os.getcwd(), "dataset")
                    if os.path.exists(data_dir):
                        down_sampled_dir = (
                            f"0.{'50' if scale == '2' else '25'}down_sampled"
                        )
                        dataset_config["csv_input_dir"] = os.path.join(
                            data_dir, down_sampled_dir
                        )

        self._suggest_image_comparison_defaults(config)

        return config

    def _suggest_image_comparison_defaults(self, config: Dict[str, Any]) -> None:
        working_dir = config.get("working_dir", os.getcwd())

        common_dirs = {
            "lr": ["lr", "low_resolution", "LR"],
            "bicubic": ["bicubic", "Bicubic", "BICUBIC"],
            "hr": ["hr", "high_resolution", "HR", "gt", "ground_truth"],
        }

        for scale_str in ["2", "4"]:
            scale_config = config["image_comparison"]["scale_configs"][scale_str]

            for folder_type, possible_names in common_dirs.items():
                if not scale_config.get(f"{folder_type}_dir"):

                    for name in possible_names:
                        potential_path = os.path.join(working_dir, name)
                        if os.path.isdir(potential_path):
                            scale_config[f"{folder_type}_dir"] = potential_path
                            break

    def get_custom_folder_history(self) -> List[Dict[str, Any]]:
        return self.config.get("custom_folder_history", [])

    def update_custom_folder_history(
        self, folder_name: str, folder_path: str, checked: bool = True
    ) -> bool:
        history = self.get_custom_folder_history()

        history = [
            item
            for item in history
            if not (item.get("name") == folder_name and item.get("path") == folder_path)
        ]

        history.insert(
            0, {"name": folder_name, "path": folder_path, "checked": checked}
        )

        self.config["custom_folder_history"] = history
        return self.save_config(self.config)

    def save_custom_folder_history(
        self, folders_dict: Dict[str, Dict[str, Any]]
    ) -> bool:
        history = []

        for name, info in folders_dict.items():
            path = info.get("path", "")
            checked = info.get("checked", True)
            if os.path.isdir(path):
                history.append({"name": name, "path": path, "checked": checked})

        existing_history = self.get_custom_folder_history()
        for item in existing_history:
            name = item.get("name", "")
            path = item.get("path", "")
            checked = item.get("checked", True)

            if (
                name
                and path
                and not any(
                    h.get("name") == name and h.get("path") == path for h in history
                )
            ):
                if os.path.isdir(path):
                    history.append({"name": name, "path": path, "checked": checked})

        self.config["custom_folder_history"] = history
        return self.save_config(self.config)

    def get_latest_custom_folder_path(self) -> str:
        history = self.get_custom_folder_history()
        if history:
            return history[0].get("path", "")
        return self.get_path("working_dir")
