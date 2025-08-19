import os
import pandas as pd
from tensorboard.backend.event_processing import event_accumulator
from datetime import datetime


def export_tensorboard_to_csv(log_dir, output_dir=None):
    """
    TensorBoardログをCSVファイルに出力
    """
    if output_dir is None:
        output_dir = log_dir

    print(f"Reading TensorBoard logs from: {log_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    # EventAccumulatorを作成
    ea = event_accumulator.EventAccumulator(log_dir)
    ea.Reload()

    # Loss系とMetrics系のタグを定義
    loss_tags = [
        "losses/l_g_pix",
        "losses/l_g_percep",
        "losses/l_g_gan",
        "losses/l_d_real",
        "losses/l_d_fake",
        "out_d_real",
        "out_d_fake",
    ]

    metrics_tags = [
        "metrics/validation/psnr",
        "metrics/validation/ssim",
        "metrics/validation/lpips",
    ]

    # Loss用DataFrame作成
    print("Processing loss data...")
    loss_data = {}

    for tag in loss_tags:
        scalar_events = ea.Scalars(tag)
        # タグ名を短縮（losses/やout_を除去）
        column_name = tag.replace("losses/", "").replace("out_", "out_")

        loss_data[column_name] = {
            "step": [event.step for event in scalar_events],
            "wall_time": [event.wall_time for event in scalar_events],
            "value": [event.value for event in scalar_events],
        }
        print(f"  {tag}: {len(scalar_events)} points")

    # Lossデータを統合
    loss_df_list = []
    for column_name, data in loss_data.items():
        df = pd.DataFrame(
            {
                "step": data["step"],
                "wall_time": data["wall_time"],
                column_name: data["value"],
            }
        )
        loss_df_list.append(df)

    # stepでマージ
    loss_df = loss_df_list[0]
    for df in loss_df_list[1:]:
        loss_df = pd.merge(loss_df, df, on=["step", "wall_time"], how="outer")

    loss_df = loss_df.sort_values("step").reset_index(drop=True)

    # Metrics用DataFrame作成
    print("\nProcessing metrics data...")
    metrics_data = {}

    for tag in metrics_tags:
        scalar_events = ea.Scalars(tag)
        # タグ名を短縮（metrics/validation/を除去）
        column_name = tag.replace("metrics/validation/", "")

        metrics_data[column_name] = {
            "step": [event.step for event in scalar_events],
            "wall_time": [event.wall_time for event in scalar_events],
            "value": [event.value for event in scalar_events],
        }
        print(f"  {tag}: {len(scalar_events)} points")

    # Metricsデータを統合
    metrics_df_list = []
    for column_name, data in metrics_data.items():
        df = pd.DataFrame(
            {
                "step": data["step"],
                "wall_time": data["wall_time"],
                column_name: data["value"],
            }
        )
        metrics_df_list.append(df)

    # stepでマージ
    metrics_df = metrics_df_list[0]
    for df in metrics_df_list[1:]:
        metrics_df = pd.merge(metrics_df, df, on=["step", "wall_time"], how="outer")

    metrics_df = metrics_df.sort_values("step").reset_index(drop=True)

    # CSV出力
    print("\nExporting to CSV files...")

    # wall_timeを読みやすい形式に変換（オプション列として追加）
    loss_df["datetime"] = pd.to_datetime(loss_df["wall_time"], unit="s")
    metrics_df["datetime"] = pd.to_datetime(metrics_df["wall_time"], unit="s")

    # CSV出力
    loss_csv_path = os.path.join(output_dir, "losses.csv")
    metrics_csv_path = os.path.join(output_dir, "metrics.csv")

    loss_df.to_csv(loss_csv_path, index=False)
    metrics_df.to_csv(metrics_csv_path, index=False)

    print(f"✓ Losses CSV exported: {loss_csv_path}")
    print(f"  Shape: {loss_df.shape}")
    print(f"  Columns: {list(loss_df.columns)}")

    print(f"✓ Metrics CSV exported: {metrics_csv_path}")
    print(f"  Shape: {metrics_df.shape}")
    print(f"  Columns: {list(metrics_df.columns)}")

    # サンプルデータ表示
    print("\n" + "=" * 60)
    print("Sample data preview:")
    print("=" * 60)

    print("\nLosses (first 5 rows):")
    print(loss_df.head())

    print("\nMetrics (first 5 rows):")
    print(metrics_df.head())

    return loss_df, metrics_df


if __name__ == "__main__":
    # ログディレクトリのパス
    log_dir = r"D:\yamamoto\Real-ESRGAN-sicm\tb_logger\finetune_csv_x4_3.1.0"

    # 出力ディレクトリ（同じディレクトリに出力）
    output_dir = log_dir

    # ディレクトリが存在するかチェック
    if not os.path.exists(log_dir):
        print(f"Error: Directory {log_dir} does not exist!")
        exit(1)

    try:
        loss_df, metrics_df = export_tensorboard_to_csv(log_dir, output_dir)
        print("\n✓ Export completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure pandas and tensorboard are installed:")
        print("pip install pandas tensorboard")
