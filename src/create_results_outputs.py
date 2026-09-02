from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error


# Paths
RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
RESULTS_DIR.mkdir(exist_ok=True)
FIGURES_DIR.mkdir(exist_ok=True)
DATA_DIR = Path("data/processed")
SEEDS = [1, 7, 21, 42, 99]

def load_lstm_forecasts(target, hidden_size, learning_rate):
    forecasts = []

    for seed in SEEDS:
        path = DATA_DIR / (
            f"lstm_{target}_"
            f"h{hidden_size}_"
            f"lr{learning_rate}_"
            f"seed{seed}_"
            f"test_forecasts.csv"
        )

        df = pd.read_csv(path, parse_dates=["week_ending"],)
        df = df.rename(columns={"predicted": f"predicted_seed_{seed}",})

        if not forecasts:
            forecasts.append(df[["week_ending", "actual", f"predicted_seed_{seed}"]])
        else:
            forecasts.append(df[["week_ending", f"predicted_seed_{seed}"]])

    combined = forecasts[0]

    for forecast in forecasts[1:]:
        combined = combined.merge(
            forecast,
            on="week_ending",
            validate="one_to_one",
        )

    prediction_columns = [f"predicted_seed_{seed}"for seed in SEEDS]
    combined["lstm_mean_prediction"] = (combined[prediction_columns].mean(axis=1))
    combined["lstm_prediction_std"] = (combined[prediction_columns].std(axis=1, ddof=1))

    return combined

def calculate_seed_metrics(
    target,
    hidden_size,
    learning_rate,
):
    results = []

    for seed in SEEDS:
        path = DATA_DIR / (
            f"lstm_{target}_"
            f"h{hidden_size}_"
            f"lr{learning_rate}_"
            f"seed{seed}_"
            f"test_forecasts.csv"
        )

        df = pd.read_csv(path)

        mae = mean_absolute_error(df["actual"], df["predicted"],)
        rmse = np.sqrt(mean_squared_error(df["actual"],df["predicted"],))
        results.append({"seed": seed, "mae": mae, "rmse": rmse,})

    return pd.DataFrame(results)

def calculate_garch_metrics(path):
    df = pd.read_csv(path, parse_dates=["week_ending"],)
    mae = mean_absolute_error(df["actual"], df["predicted"],)
    rmse = np.sqrt(mean_squared_error(df["actual"], df["predicted"],))
    return df, mae, rmse

def create_forecast_plot(
    target_name,
    garch,
    lstm,
    output_path,
):
    merged = garch.merge(
        lstm[
            [
                "week_ending",
                "lstm_mean_prediction",
                "lstm_prediction_std",
            ]
        ],
        on="week_ending",
        validate="one_to_one",
    )

    plt.figure(figsize=(12, 6))
    plt.plot(merged["week_ending"],merged["actual"],label="Actual",)
    plt.plot(merged["week_ending"],merged["predicted"],label="GARCH",)
    plt.plot(merged["week_ending"],merged["lstm_mean_prediction"],label="LSTM mean",)
    plt.fill_between(
        merged["week_ending"],
        (
            merged["lstm_mean_prediction"]
            - merged["lstm_prediction_std"]
        ),
        (
            merged["lstm_mean_prediction"]
            + merged["lstm_prediction_std"]
        ),
        alpha=0.2,
        label="LSTM ±1 SD",
    )

    plt.title(target_name)
    plt.xlabel("Week")
    plt.ylabel("Volatility")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

# Primary target
primary_lstm = load_lstm_forecasts(target="primary", hidden_size=16, learning_rate=0.001,)
primary_lstm_metrics = calculate_seed_metrics(target="primary", hidden_size=16, learning_rate=0.001,)
primary_garch, primary_garch_mae, primary_garch_rmse = (calculate_garch_metrics(DATA_DIR / "garch_primary_test_forecasts.csv"))

# Robustness target
robustness_lstm = load_lstm_forecasts(target="robustness", hidden_size=32, learning_rate=0.001,)
robustness_lstm_metrics = calculate_seed_metrics(target="robustness", hidden_size=32, learning_rate=0.001,)
(robustness_garch, robustness_garch_mae, robustness_garch_rmse,) = calculate_garch_metrics(DATA_DIR / "garch_robustness_test_forecasts.csv")

# Final comparison table
comparison = pd.DataFrame([
    {
        "target": "Primary",
        "model": "GARCH(1,2)-t",
        "mae_mean": primary_garch_mae,
        "mae_std": np.nan,
        "rmse_mean": primary_garch_rmse,
        "rmse_std": np.nan,
    },
    {
        "target": "Primary",
        "model": "Multivariate LSTM",
        "mae_mean": primary_lstm_metrics["mae"].mean(),
        "mae_std": primary_lstm_metrics["mae"].std(ddof=1),
        "rmse_mean": primary_lstm_metrics["rmse"].mean(),
        "rmse_std": primary_lstm_metrics["rmse"].std(ddof=1),
    },
    {
        "target": "Robustness",
        "model": "GARCH(1,2)-t",
        "mae_mean": robustness_garch_mae,
        "mae_std": np.nan,
        "rmse_mean": robustness_garch_rmse,
        "rmse_std": np.nan,
    },
    {
        "target": "Robustness",
        "model": "Multivariate LSTM",
        "mae_mean": robustness_lstm_metrics["mae"].mean(),
        "mae_std": robustness_lstm_metrics["mae"].std(ddof=1),
        "rmse_mean": robustness_lstm_metrics["rmse"].mean(),
        "rmse_std": robustness_lstm_metrics["rmse"].std(ddof=1),
    },
])

comparison.to_csv(RESULTS_DIR / "final_model_comparison.csv", index=False,)

# Save mean LSTM forecasts
primary_lstm.to_csv(RESULTS_DIR / "primary_lstm_final_forecasts.csv", index=False,)
robustness_lstm.to_csv(RESULTS_DIR / "robustness_lstm_final_forecasts.csv", index=False,)

# Figures
create_forecast_plot(
    target_name="Primary Four-Week Volatility Forecasts",
    garch=primary_garch,
    lstm=primary_lstm,
    output_path=FIGURES_DIR
    / "primary_garch_vs_lstm.png",
)

create_forecast_plot(
    target_name="Robustness One-Week Squared Return Forecasts",
    garch=robustness_garch,
    lstm=robustness_lstm,
    output_path=FIGURES_DIR
    / "robustness_garch_vs_lstm.png",
)


print("Final Model Comparison")
print(comparison.to_string(index=False, float_format=lambda x: f"{x:.6f}",))

print("\nSaved:")
print("results/final_model_comparison.csv")
print("results/primary_lstm_final_forecasts.csv")
print("results/robustness_lstm_final_forecasts.csv")
print("results/figures/primary_garch_vs_lstm.png")
print("results/figures/robustness_garch_vs_lstm.png")