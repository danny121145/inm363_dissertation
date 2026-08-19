import pandas as pd
from arch import arch_model
from config import WEEKLY_DATA_PATH, TRAIN_END, VALIDATION_END, VALIDATION_START, TEST_START
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error


#load final weekly modelling dataset
data = pd.read_csv(WEEKLY_DATA_PATH, parse_dates=["week_ending"])
data = data.sort_values("week_ending").reset_index(drop=True)

#use weekly log returns for GARCH model
returns = data[["week_ending", "log_return"]].dropna().copy()

#training period only
train = returns[returns["week_ending"] <= pd.Timestamp(TRAIN_END)].copy()

print(f"Rows: {len(train)}")
print(f"Date Range: {train['week_ending'].min().date()} to {train['week_ending'].max().date()}")
print(f"missing log returns: {train['log_return'].isna().sum()}")

#scale returns to percentage
train_returns = train["log_return"] * 100

#candidate specifications for GARCH model
candidates = [
    {"p": 1, "q": 1, "dist": "normal"},
    {"p": 1, "q": 1, "dist": "t"},
    {"p": 1, "q": 2, "dist": "normal"},
    {"p": 1, "q": 2, "dist": "t"},
    {"p": 2, "q": 1, "dist": "normal"},
    {"p": 2, "q": 1, "dist": "t"},
]

results = []

for candidate in candidates:
    p = candidate["p"]
    q = candidate["q"]
    dist = candidate["dist"]

    model = arch_model(
        train_returns,
        mean="Constant",
        vol="GARCH",
        p=p,
        q=q,
        dist=dist
    )

    fitted_model = model.fit(disp="off")
    results.append({
        "model": f"GARCH({p},{q}) - {dist}",
        "distribution": dist,
        "log_likelihood": fitted_model.loglikelihood,
        "aic": fitted_model.aic,
        "bic": fitted_model.bic,
        "convergence_flag": fitted_model.convergence_flag
    })

comparison = pd.DataFrame(results)
comparison = comparison.sort_values(by="aic").reset_index(drop=True)

print("GARCH Model Comparison:")
print(comparison.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

# Candidates taken forward to validation
validation_candidates = [
    {"p": 1, "q": 1, "dist": "t"},
    {"p": 1, "q": 2, "dist": "t"},
]

def validation_forecasts(data, p, q, dist):
    primary_results = []
    robustness_results = []
    validation_dates = data.loc[(data["week_ending"] >= pd.Timestamp(VALIDATION_START)) & (data["week_ending"] <= pd.Timestamp(VALIDATION_END)), "week_ending",]
    for forecast_date in validation_dates:
        # All returns available up to the forecast date
        history = data.loc[data["week_ending"] <= forecast_date, "log_return",].dropna()

        # GARCH fitted using percentage returns
        history_pct = history * 100
        model = arch_model(
            history_pct,
            mean="Constant",
            vol="GARCH",
            p=p,
            q=q,
            dist=dist,
        )
        fitted = model.fit(disp="off")

        # Forecast next four weekly variances
        forecasts = fitted.forecast(horizon=4, reindex=False,)
        forecast_variances = forecasts.variance.iloc[-1].to_numpy()

        # Primary target: future four-week volatility
        actual_primary = data.loc[data["week_ending"] == forecast_date, "target_volatility_4w",].iloc[0]
        if pd.notna(actual_primary) and forecast_date <= pd.Timestamp("2022-12-02"):

            # Convert percentage variance back to decimal volatility
            predicted_primary = (np.sqrt(np.mean(forecast_variances)) / 100)
            primary_results.append({"week_ending": forecast_date, "actual": actual_primary, "predicted": predicted_primary,})

        # Robustness target: next-week squared return
        actual_robustness = data.loc[data["week_ending"] == forecast_date, "target_squared_volatility_1w",].iloc[0]
        if pd.notna(actual_robustness) and forecast_date <= pd.Timestamp("2022-12-23"):

            # h.1 is forecast variance for the next week. Variance is in percentage-return units squared, so divide by 100^2 to return to decimal units.
            predicted_robustness = forecast_variances[0] / 10000
            robustness_results.append({
                "week_ending": forecast_date,
                "actual": actual_robustness,
                "predicted": predicted_robustness,
            })
    return (pd.DataFrame(primary_results), pd.DataFrame(robustness_results),)

def calculate_metrics(results):
    mae = mean_absolute_error(results["actual"], results["predicted"],)
    rmse = np.sqrt(mean_squared_error(results["actual"], results["predicted"],))
    return mae, rmse

print("Validation Forecast Comparison")
validation_summary = []
for candidate in validation_candidates:
    p = candidate["p"]
    q = candidate["q"]
    dist = candidate["dist"]

    primary_results, robustness_results = validation_forecasts(
        data=data,
        p=p,
        q=q,
        dist=dist,
    )
    primary_mae, primary_rmse = calculate_metrics(primary_results)
    robustness_mae, robustness_rmse = calculate_metrics(robustness_results)

    validation_summary.append({
        "model": f"GARCH({p},{q}) - {dist}",
        "primary_mae": primary_mae,
        "primary_rmse": primary_rmse,
        "robustness_mae": robustness_mae,
        "robustness_rmse": robustness_rmse,
    })
validation_summary = pd.DataFrame(validation_summary)
print(validation_summary.to_string(index=False, float_format=lambda x: f"{x:.6f}",))

# Final test evaluation
FINAL_P = 1
FINAL_Q = 2
FINAL_DIST = "t"
PRIMARY_TEST_END = pd.Timestamp("2026-07-03")
ROBUSTNESS_TEST_END = pd.Timestamp("2026-07-24")

def test_forecasts(data):
    primary_results = []
    robustness_results = []

    test_dates = data.loc[data["week_ending"] >= pd.Timestamp(TEST_START), "week_ending",]
    for forecast_date in test_dates:

        # Use all returns available up to the forecast date
        history = data.loc[data["week_ending"] <= forecast_date, "log_return",].dropna()
        history_pct = history * 100
        model = arch_model(
            history_pct,
            mean="Constant",
            vol="GARCH",
            p=FINAL_P,
            q=FINAL_Q,
            dist=FINAL_DIST,
        )
        fitted = model.fit(disp="off")

        # Forecast the next four weekly variances
        forecasts = fitted.forecast(horizon=4, reindex=False,)

        forecast_variances = (forecasts.variance.iloc[-1].to_numpy())

        # Primary target
        actual_primary = data.loc[data["week_ending"] == forecast_date, "target_volatility_4w",].iloc[0]

        if (pd.notna(actual_primary) and forecast_date <= PRIMARY_TEST_END):
            predicted_primary = (np.sqrt(np.mean(forecast_variances)) / 100)

            primary_results.append({"week_ending": forecast_date,"actual": actual_primary, "predicted": predicted_primary,})

        # Robustness target
        actual_robustness = data.loc[data["week_ending"] == forecast_date, "target_squared_volatility_1w",].iloc[0]

        if (
            pd.notna(actual_robustness) and forecast_date <= ROBUSTNESS_TEST_END):
            predicted_robustness = (forecast_variances[0] / 10000)

            robustness_results.append({"week_ending": forecast_date, "actual": actual_robustness, "predicted": predicted_robustness,})

    return (pd.DataFrame(primary_results),pd.DataFrame(robustness_results),)

test_primary, test_robustness = test_forecasts(data)
test_primary_mae, test_primary_rmse = calculate_metrics(test_primary)
test_robustness_mae, test_robustness_rmse = calculate_metrics(test_robustness)

print("Final GARCH Test Results")
print(f"Model: GARCH({FINAL_P},{FINAL_Q}) - "f"{FINAL_DIST}")
print("Primary Target")
print(f"Forecasts: {len(test_primary)}")
print(f"MAE: {test_primary_mae:.6f}")
print(f"RMSE: {test_primary_rmse:.6f}")
print("Robustness Target")
print(f"Forecasts: {len(test_robustness)}")
print(f"MAE: {test_robustness_mae:.6f}")
print(f"RMSE: {test_robustness_rmse:.6f}")

# Save final GARCH test forecasts
test_primary.to_csv("data/processed/garch_primary_test_forecasts.csv",index=False,)
test_robustness.to_csv("data/processed/garch_robustness_test_forecasts.csv", index=False,)