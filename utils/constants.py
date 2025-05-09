EXPERIMENT_DATA_FILE = "experiment_settings.csv"
EXPERIMENT_COLUMNS = [
    "version",
    "total_iter",
    "model_save_freq",
    "batch_size",
    "num_train_images",
    "best_iter",
]
EXPERIMENT_COLUMN_NAMES = [
    "バージョン",
    "総Iter",
    "保存頻度",
    "バッチサイズ",
    "画像数",
    "最適Iter(参考)",
]

SCALE_CONFIGS_DEFAULT = {
    2: {
        "csv_input_dir": "",
        "csv_output_dir": "x2csvcsv_128_finetuned",
    },
    4: {
        "csv_input_dir": "",
        "csv_output_dir": "x4csvcsv_128_finetuned",
    },
}
