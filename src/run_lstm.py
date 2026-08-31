import copy
import random
import numpy as np
import torch
import torch.nn as nn
from config import SEED
import argparse
from prepare_lstm_sequence import primary_scaled, robustness_scaled
import pandas as pd
import wandb
from sklearn.metrics import mean_absolute_error, mean_squared_error

parser = argparse.ArgumentParser()

parser.add_argument(
    "--target",
    choices=["primary", "robustness"],
    required=True,
)

parser.add_argument(
    "--seed",
    type=int,
    default=SEED,
)

parser.add_argument(
    "--hidden-size",
    type=int,
    default=32,
)

parser.add_argument(
    "--learning-rate",
    type=float,
    default=0.001,
)

args = parser.parse_args()
RUN_SEED = args.seed
HIDDEN_SIZE = args.hidden_size
LEARNING_RATE = args.learning_rate

if args.target == "primary":
    scaled_data = primary_scaled
else:
    scaled_data = robustness_scaled

# Reproducibility
random.seed(RUN_SEED)
np.random.seed(RUN_SEED)
torch.manual_seed(RUN_SEED)
torch.use_deterministic_algorithms(True)
# Data
X_train = torch.tensor(scaled_data["X_train"],dtype=torch.float32,)
y_train = torch.tensor(scaled_data["y_train"],dtype=torch.float32,).unsqueeze(1)
X_validation = torch.tensor(scaled_data["X_validation"],dtype=torch.float32,)
y_validation = torch.tensor(scaled_data["y_validation"], dtype=torch.float32, ).unsqueeze(1)


# Basic LSTM model
class LSTMRegressor(nn.Module):
    def __init__(self, input_size, hidden_size=32,):
        super().__init__()

        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=1, batch_first=True,)
        self.output_layer = nn.Linear(hidden_size, 1,)

    def forward(self, x):
        lstm_output, _ = self.lstm(x)

        # Use final time step
        final_output = lstm_output[:, -1, :]
        prediction = self.output_layer(final_output)
        return prediction

# Training configuration
MAX_EPOCHS = 100
PATIENCE = 10

best_validation_loss = float("inf")
best_model_state = None
epochs_without_improvement = 0
stopping_epoch = MAX_EPOCHS

run = wandb.init(
    project = "inm363-dissertation",
    name=(
        f"{args.target}"
        f"-h{HIDDEN_SIZE}"
        f"-lr{LEARNING_RATE}"
        f"-seed{RUN_SEED}"
    ),
    config={
        "target": args.target,
        "sequence_length": 12,
        "hidden_size": HIDDEN_SIZE,
        "learning_rate": LEARNING_RATE,
        "max_epochs": MAX_EPOCHS,
        "patience": PATIENCE,
        "seed": RUN_SEED,
        "n_features": X_train.shape[2],
    },
)

model = LSTMRegressor(input_size=X_train.shape[2], hidden_size=HIDDEN_SIZE,)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE,)

# Training loop
for epoch in range(MAX_EPOCHS):
    model.train()
    optimizer.zero_grad()
    train_predictions = model(X_train)
    train_loss = criterion(train_predictions, y_train,)
    train_loss.backward()
    optimizer.step()

    # Validation
    model.eval()

    with torch.no_grad():

        validation_predictions = model(X_validation)
        validation_loss = criterion(validation_predictions,y_validation, )

    print(
        f"Epoch {epoch + 1:03d} | "
        f"Train Loss: {train_loss.item():.6f} | "
        f"Validation Loss: {validation_loss.item():.6f}"
    )

    run.log({
        "epoch": epoch + 1,
        "train_loss": train_loss.item(),
        "validation_loss": validation_loss.item(),
    })
    # Early stopping
    if validation_loss.item() < best_validation_loss:
        best_validation_loss = validation_loss.item()
        best_model_state = copy.deepcopy(model.state_dict())
        epochs_without_improvement = 0
    else:
        epochs_without_improvement += 1

    if epochs_without_improvement >= PATIENCE:
        stopping_epoch = epoch + 1
        print(f"\nEarly stopping at epoch {stopping_epoch}")
        break

# Restore best model
model.load_state_dict(best_model_state)
print("Basic LSTM training complete.")
print(f"Best validation loss: " f"{best_validation_loss:.6f}")

# Evaluation
model.eval()

with torch.no_grad():
    validation_predictions_scaled = model(X_validation).squeeze(1).numpy()
    X_test = torch.tensor(scaled_data["X_test"], dtype=torch.float32,)
    test_predictions_scaled = model(X_test).squeeze(1).numpy()

# Convert predictions back to original target units
target_scaler = scaled_data["target_scaler"]
validation_predictions = target_scaler.inverse_transform(validation_predictions_scaled.reshape(-1, 1)).flatten()
test_predictions = target_scaler.inverse_transform(test_predictions_scaled.reshape(-1, 1)).flatten()

# Actual targets in original units
validation_actual = target_scaler.inverse_transform(scaled_data["y_validation"].reshape(-1, 1)).flatten()
test_actual = target_scaler.inverse_transform(scaled_data["y_test"].reshape(-1, 1)).flatten()

# Metrics
validation_mae = mean_absolute_error(validation_actual,validation_predictions,)
validation_rmse = np.sqrt(mean_squared_error(validation_actual, validation_predictions,))
test_mae = mean_absolute_error(test_actual, test_predictions,)
test_rmse = np.sqrt(mean_squared_error(test_actual, test_predictions,))

print(f"{args.target.capitalize()} LSTM Results")

print("Validation")
print(f"Forecasts: {len(validation_predictions)}")
print(f"MAE: {validation_mae:.6f}")
print(f"RMSE: {validation_rmse:.6f}")

print("Test")
print(f"Forecasts: {len(test_predictions)}")
print(f"MAE: {test_mae:.6f}")
print(f"RMSE: {test_rmse:.6f}")

run.log({
    "best_validation_loss": best_validation_loss,
    "validation_mae": validation_mae,
    "validation_rmse": validation_rmse,
    "test_mae": test_mae,
    "test_rmse": test_rmse,
    "stopping_epoch": stopping_epoch,
})
# Save predictions
validation_results = pd.DataFrame({"week_ending": scaled_data["validation_dates"], "actual": validation_actual, "predicted": validation_predictions,})
test_results = pd.DataFrame({"week_ending": scaled_data["test_dates"], "actual": test_actual,"predicted": test_predictions,})

validation_result_dates = pd.to_datetime(
    validation_results["week_ending"]
).to_numpy(dtype="datetime64[ns]")

expected_validation_dates = pd.to_datetime(
    scaled_data["validation_dates"]
).to_numpy(dtype="datetime64[ns]")

if not np.array_equal(
    validation_result_dates,
    expected_validation_dates,
):
    raise ValueError(
        "Validation prediction dates are misaligned."
    )

test_result_dates = pd.to_datetime(
    test_results["week_ending"]
).to_numpy(dtype="datetime64[ns]")

expected_test_dates = pd.to_datetime(
    scaled_data["test_dates"]
).to_numpy(dtype="datetime64[ns]")

if not np.array_equal(
    test_result_dates,
    expected_test_dates,
):
    raise ValueError(
        "Test prediction dates are misaligned."
    )

validation_results.to_csv(f"data/processed/lstm_{args.target}_validation_forecasts.csv",index=False,)
test_results.to_csv(f"data/processed/lstm_{args.target}_test_forecasts.csv",index=False,)
print(f"Saved {args.target.capitalize()} LSTM forecasts.")

run.finish()