import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np


def plot_losses(df, output_dir):
    """
    Loss系メトリクスをプロット
    """
    # Loss系のカラム名
    loss_columns = [
        "l_g_pix",
        "l_g_percep",
        "l_g_gan",
        "l_d_real",
        "l_d_fake",
        "out_d_real",
        "out_d_fake",
    ]

    # サブプロットのレイアウト（3x3で7個）
    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    fig.suptitle("Training Losses", fontsize=16, fontweight="bold")

    # axesを1次元配列に変換
    axes = axes.flatten()

    for i, column in enumerate(loss_columns):
        ax = axes[i]
        if column in df.columns:
            ax.plot(df["step"], df[column], linewidth=0.8, color="blue", alpha=0.8)
            ax.set_title(column, fontsize=12, fontweight="bold")
            ax.set_xlabel("Step")
            ax.set_ylabel("Loss Value")
            ax.grid(True, alpha=0.3)
            ax.ticklabel_format(style="scientific", axis="y", scilimits=(0, 0))
        else:
            ax.text(
                0.5,
                0.5,
                f"{column}\nNot Found",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=10,
            )
            ax.set_title(column, fontsize=12)

    # 余ったサブプロットを非表示
    for i in range(len(loss_columns), len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()

    # 保存
    loss_plot_path = os.path.join(output_dir, "losses_plot.png")
    plt.savefig(loss_plot_path, dpi=300, bbox_inches="tight")
    print(f"✓ Losses plot saved: {loss_plot_path}")

    return fig


def plot_metrics(df, output_dir):
    """
    Metrics系メトリクスをプロット
    """
    # Metrics系のカラム名
    metrics_columns = ["psnr", "ssim", "lpips"]
    metrics_labels = ["PSNR (dB)", "SSIM", "LPIPS"]
    colors = ["green", "orange", "red"]

    # サブプロットのレイアウト（1x3）
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Validation Metrics", fontsize=16, fontweight="bold")

    # 最大・最小値を記録
    best_values = {}

    for i, (column, label, color) in enumerate(
        zip(metrics_columns, metrics_labels, colors)
    ):
        ax = axes[i]
        if column in df.columns:
            ax.plot(df["step"], df[column], linewidth=0.8, color=color, alpha=0.8)
            ax.set_xlabel("Step")
            ax.set_ylabel(label)
            ax.grid(True, alpha=0.3)

            # 最大値・最小値の計算
            if column == "lpips":  # LPIPSは最小値が最良
                best_idx = df[column].idxmin()
                best_value = df[column].min()
                best_step = df.loc[best_idx, "step"]
                best_values[column] = {
                    "step": best_step,
                    "value": best_value,
                    "type": "min",
                }

                # LPIPSは軸を反転（小さいほど上に表示）
                ax.invert_yaxis()

                # タイトルに最小値情報を含める
                title_text = f"{label}\nMin: {best_value:.4f} (Step {best_step})"

            else:  # PSNRとSSIMは最大値が最良
                best_idx = df[column].idxmax()
                best_value = df[column].max()
                best_step = df.loc[best_idx, "step"]
                best_values[column] = {
                    "step": best_step,
                    "value": best_value,
                    "type": "max",
                }

                # タイトルに最大値情報を含める
                title_text = f"{label}\nMax: {best_value:.4f} (Step {best_step})"

            # タイトル設定
            ax.set_title(title_text, fontsize=11, fontweight="bold")
        else:
            ax.text(
                0.5,
                0.5,
                f"{column}\nNot Found",
                ha="center",
                va="center",
                transform=ax.transAxes,
                fontsize=10,
            )
            ax.set_title(label, fontsize=11)

    plt.tight_layout()

    # 保存
    metrics_plot_path = os.path.join(output_dir, "metrics_plot.png")
    plt.savefig(metrics_plot_path, dpi=300, bbox_inches="tight")
    print(f"✓ Metrics plot saved: {metrics_plot_path}")

    # 最大・最小値の情報を出力
    print("\n" + "=" * 50)
    print("BEST VALIDATION METRICS:")
    print("=" * 50)
    for metric, info in best_values.items():
        metric_name = metric.upper()
        value_type = "Maximum" if info["type"] == "max" else "Minimum"
        print(f"{metric_name} {value_type}: {info['value']:.6f} at step {info['step']}")
    print("=" * 50)

    return fig, best_values


def plot_csv_data(csv_dir, output_dir=None):
    """
    CSVファイルからデータを読み込んでプロット
    """
    if output_dir is None:
        output_dir = csv_dir

    losses_csv_path = os.path.join(csv_dir, "losses.csv")
    metrics_csv_path = os.path.join(csv_dir, "metrics.csv")

    print(f"Reading CSV files from: {csv_dir}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    # CSVファイルの存在確認
    if not os.path.exists(losses_csv_path):
        print(f"Error: {losses_csv_path} not found!")
        return

    if not os.path.exists(metrics_csv_path):
        print(f"Error: {metrics_csv_path} not found!")
        return

    # CSVファイル読み込み
    print("Loading CSV files...")
    losses_df = pd.read_csv(losses_csv_path)
    metrics_df = pd.read_csv(metrics_csv_path)

    print(f"Losses data shape: {losses_df.shape}")
    print(f"Metrics data shape: {metrics_df.shape}")

    # データの概要表示
    print("\nLosses data columns:", list(losses_df.columns))
    print("Metrics data columns:", list(metrics_df.columns))

    print(f"\nStep range: {losses_df['step'].min()} - {losses_df['step'].max()}")
    print(f"Total steps: {len(losses_df)}")

    # プロット作成
    print("\nCreating plots...")

    # Matplotlibのスタイル設定
    plt.style.use("default")
    plt.rcParams["font.size"] = 10
    plt.rcParams["axes.titlesize"] = 12
    plt.rcParams["axes.labelsize"] = 10
    plt.rcParams["legend.fontsize"] = 9

    # Lossesプロット
    losses_fig = plot_losses(losses_df, output_dir)

    # Metricsプロット
    metrics_fig, best_values = plot_metrics(metrics_df, output_dir)

    # プロット表示はしない（保存のみ）
    plt.close("all")  # メモリ節約のため閉じる

    print("\n✓ All plots created and saved successfully!")

    return losses_fig, metrics_fig, best_values


def main():
    """
    メイン関数
    """
    # CSVファイルがあるディレクトリ
    csv_dir = r"D:\yamamoto\Real-ESRGAN-sicm\tb_logger\finetune_csv_x4_3.2.0"

    # 出力ディレクトリ（同じディレクトリに保存）
    output_dir = csv_dir

    try:
        losses_fig, metrics_fig, best_values = plot_csv_data(csv_dir, output_dir)

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure pandas and matplotlib are installed:")
        print("pip install pandas matplotlib")


if __name__ == "__main__":
    main()
