import os
from tensorboard.backend.event_processing import event_accumulator


def explore_tensorboard_logs(log_dir):
    """
    TensorBoardログファイルを探索して利用可能なメトリクス名を表示
    """
    print(f"Exploring TensorBoard logs in: {log_dir}")
    print("=" * 60)

    # EventAccumulatorを作成
    ea = event_accumulator.EventAccumulator(log_dir)
    ea.Reload()  # ログファイルを読み込み

    # 利用可能なスカラータグを取得
    scalar_tags = ea.Tags()["scalars"]

    print(f"Found {len(scalar_tags)} scalar metrics:")
    print("-" * 40)

    for tag in scalar_tags:
        print(f"Tag: {tag}")

    print("\n" + "=" * 60)
    print("Sample data for each metric:")
    print("=" * 60)

    # 各タグのサンプルデータを表示
    for tag in scalar_tags:
        scalar_events = ea.Scalars(tag)
        print(f"\nMetric: {tag}")
        print(f"Total data points: {len(scalar_events)}")

        # 最初の3つのデータポイントを表示
        for i, event in enumerate(scalar_events[:3]):
            step = event.step
            wall_time = event.wall_time
            value = event.value
            print(
                f"  Point {i+1}: step={step}, wall_time={wall_time:.2f}, value={value:.6f}"
            )

        if len(scalar_events) > 3:
            print(f"  ... and {len(scalar_events) - 3} more points")

        print("-" * 40)


if __name__ == "__main__":
    # ログディレクトリのパス
    log_dir = r"D:\yamamoto\Real-ESRGAN-sicm\tb_logger\finetune_csv_x4_3.1.0"

    # ディレクトリが存在するかチェック
    if not os.path.exists(log_dir):
        print(f"Error: Directory {log_dir} does not exist!")
        exit(1)

    # tfeventsファイルが存在するかチェック
    tfevents_files = [
        f for f in os.listdir(log_dir) if f.startswith("events.out.tfevents")
    ]
    if not tfevents_files:
        print(f"Error: No tfevents files found in {log_dir}")
        exit(1)

    print(f"Found tfevents files: {tfevents_files}")
    print()

    try:
        explore_tensorboard_logs(log_dir)
    except Exception as e:
        print(f"Error reading TensorBoard logs: {e}")
        print("Make sure tensorboard is installed: pip install tensorboard")
