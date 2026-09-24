# Forecasting USD/IRR Exchange-Rate Volatility

MSc Artificial Intelligence dissertation project comparing a traditional GARCH volatility model with a multivariate LSTM for forecasting weekly free-market USD/IRR exchange-rate volatility.

## Research Question

Can a machine-learning time-series model provide improved performance compared with a traditional statistical model when forecasting exchange-rate volatility in Iran?

## Final Experimental Design

The final comparison uses:

- **GARCH(1,2) with Student's t innovations** as the statistical benchmark.
- **Multivariate LSTM** using 12 weeks of historical information and eight input features.

Two forecasting tasks are evaluated:

- **Primary target:** `target_volatility_4w` — standard deviation of the following four weekly USD/IRR log returns.
- **Robustness target:** `target_squared_volatility_1w` — squared USD/IRR log return for the following week.

The original project plan included an additional univariate LSTM, but this was removed after data preparation so that more time could be allocated to controlled validation, repeated LSTM runs, implementation checks and robustness testing.

## Data Sources

The modelling dataset combines four sources:

| Source | Data used |
| --- | --- |
| TGJU | Free-market USD/IRR historical exchange-rate data |
| U.S. Energy Information Administration (EIA) | Weekly Europe Brent Spot Price FOB |
| International Monetary Fund (IMF) | Monthly Iranian Consumer Price Index |
| U.S. Treasury OFAC | Iran-related Recent Actions announcements |

The TGJU snapshot contains 3,916 daily observations from 26 November 2011 to 30 July 2026. After conversion to Friday-ending weekly observations, the USD/IRR dataset contains 763 weeks from 2 December 2011 to 31 July 2026.

## LSTM Features

The final multivariate LSTM uses eight features:

- `log_return`
- `squared_return`
- `rolling_volatility_4w`
- `brent_log_return`
- `inflation_yoy`
- `sanctions_event_count`
- `sanctions_tightening_count`
- `sanctions_relief_count`

Each prediction uses the previous 12 weeks of these features.

## Chronological Evaluation

The data are split chronologically:

- Training ends: **2019-12-27**
- Validation: **2020-01-03 to 2022-12-30**
- Test begins: **2023-01-06**

Because the targets use future returns, the final observations at the training and validation boundaries are removed where necessary so that target values cannot cross into the following partition.

LSTM feature and target scalers are fitted on training data only.

## Final Model Configuration

### GARCH

The project initially compares GARCH(1,1), GARCH(1,2) and GARCH(2,1), each with Normal and Student's t innovations. GARCH(1,2)-t is selected using training and validation evidence.

During validation and test evaluation, GARCH uses an expanding window and is re-estimated at every forecast date using all returns available up to that date.

### LSTM

The LSTM contains one PyTorch LSTM layer followed by a linear output layer.

Common settings:

- Sequence length: 12 weeks
- Loss: Mean Squared Error
- Optimiser: Adam
- Maximum epochs: 100
- Early-stopping patience: 10
- Final seeds: 1, 7, 21, 42, 99

Final primary configuration:

- Hidden size: 16
- Learning rate: 0.001

Final robustness configuration:

- Hidden size: 32
- Learning rate: 0.001

## Final Test Results

| Target | Model | MAE | RMSE |
| --- | --- | ---: | ---: |
| Four-week volatility | GARCH(1,2)-t | 0.019744 | 0.025903 |
| Four-week volatility | Multivariate LSTM | 0.017671 ± 0.000529 | 0.023306 ± 0.000260 |
| Next-week squared return | GARCH(1,2)-t | 0.001966 | 0.003844 |
| Next-week squared return | Multivariate LSTM | 0.002021 ± 0.000144 | 0.003685 ± 0.000021 |

For the primary four-week target, the LSTM reduces MAE by approximately 10.5% and RMSE by approximately 10.0% relative to GARCH. The robustness experiment is mixed: GARCH has the lower MAE, while the LSTM has the lower RMSE.

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── docs/
│   ├── ai_evidence.md
│   ├── ai_use_register.md
│   ├── feature_register.md
│   ├── methodology.md
│   └── sources_register.md
└── src/
    ├── config.py
    ├── create_results_outputs.py
    ├── download_ofac_sanctions.py
    ├── download_tgju_data.py
    ├── explore_brent_oil.py
    ├── explore_inflation.py
    ├── explore_sanctions_data.py
    ├── explore_weekly_data.py
    ├── prepare_brent_oil_data.py
    ├── prepare_inflation_data.py
    ├── prepare_lstm_sequence.py
    ├── prepare_modelling_data.py
    ├── prepare_modelling_datasets.py
    ├── prepare_sanctions_data.py
    ├── prepare_tgju_data.py
    ├── prepare_weekly_data.py
    ├── prepare_weekly_sanctions_data.py
    ├── run_garch.py
    └── run_lstm.py
```

The `data/`, `results/` and local `wandb/` directories are excluded from Git version control.

## Environment Setup

The project was developed in Python. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with:

```bash
.venv\Scripts\activate
```

The LSTM training script uses Weights & Biases through `wandb.init()`, so W&B must be configured before running the LSTM experiments.

## Required Local Data Files

The following data files are not tracked by Git and must be present locally before reconstructing the full pipeline:

```text
data/
├── raw/
│   ├── usd_irr_tgju_history_raw.json
│   ├── Weekly_Europe_Brent_Spot_Price_FOB.csv
│   ├── imf_iran_cpi_monthly.csv
│   └── ofac_iran_candidate_events_raw.json
└── manual/
    └── ofac_iran_event_classifications.csv
```

The TGJU and OFAC download scripts can create their corresponding raw snapshots. The Brent and IMF raw files must be supplied from their original sources. The OFAC classification CSV is a manually reviewed project input and is required before sanctions processing can be reproduced.

## Reconstructing the Modelling Dataset

Run commands from the repository root.

### 1. Prepare the USD/IRR data

If the fixed TGJU raw snapshot is not already available:

```bash
python src/download_tgju_data.py
```

Then clean the daily data and create the weekly exchange-rate dataset:

```bash
python src/prepare_tgju_data.py
python src/prepare_weekly_data.py
```

Optional diagnostics:

```bash
python src/explore_weekly_data.py
```

### 2. Prepare Brent oil data

Place `Weekly_Europe_Brent_Spot_Price_FOB.csv` in `data/raw/`, then run:

```bash
python src/prepare_brent_oil_data.py
```

Optional diagnostics:

```bash
python src/explore_brent_oil.py
```

### 3. Prepare inflation data

Place `imf_iran_cpi_monthly.csv` in `data/raw/`, then run:

```bash
python src/prepare_inflation_data.py
```

Optional diagnostics:

```bash
python src/explore_inflation.py
```

### 4. Prepare sanctions data

If the fixed raw OFAC candidate-announcement snapshot is not already available:

```bash
python src/download_ofac_sanctions.py
```

After the manually reviewed file `data/manual/ofac_iran_event_classifications.csv` is present, run:

```bash
python src/prepare_sanctions_data.py
python src/prepare_weekly_sanctions_data.py
```

Optional diagnostics:

```bash
python src/explore_sanctions_data.py
```

### 5. Merge the modelling dataset

```bash
python src/prepare_modelling_data.py
python src/prepare_modelling_datasets.py
```

This creates the weekly modelling data used by the final models and prints the chronological split summaries.

## Running the Final Models

### GARCH

```bash
python src/run_garch.py
```

This performs the candidate comparison, chronological validation, final GARCH(1,2)-t test evaluation and saves:

```text
data/processed/garch_primary_test_forecasts.csv
data/processed/garch_robustness_test_forecasts.csv
```

### LSTM — primary target

Run the final primary configuration for all five predefined seeds:

```bash
python src/run_lstm.py --target primary --hidden-size 16 --learning-rate 0.001 --seed 1
python src/run_lstm.py --target primary --hidden-size 16 --learning-rate 0.001 --seed 7
python src/run_lstm.py --target primary --hidden-size 16 --learning-rate 0.001 --seed 21
python src/run_lstm.py --target primary --hidden-size 16 --learning-rate 0.001 --seed 42
python src/run_lstm.py --target primary --hidden-size 16 --learning-rate 0.001 --seed 99
```

### LSTM — robustness target

Run the final robustness configuration for the same five seeds:

```bash
python src/run_lstm.py --target robustness --hidden-size 32 --learning-rate 0.001 --seed 1
python src/run_lstm.py --target robustness --hidden-size 32 --learning-rate 0.001 --seed 7
python src/run_lstm.py --target robustness --hidden-size 32 --learning-rate 0.001 --seed 21
python src/run_lstm.py --target robustness --hidden-size 32 --learning-rate 0.001 --seed 42
python src/run_lstm.py --target robustness --hidden-size 32 --learning-rate 0.001 --seed 99
```

Each run writes validation and test forecast CSV files into `data/processed/`.

## Recreating the Final Tables and Figures

After the GARCH run and all ten final LSTM runs have completed:

```bash
python src/create_results_outputs.py
```

This creates:

```text
results/
├── final_model_comparison.csv
├── primary_lstm_final_forecasts.csv
├── robustness_lstm_final_forecasts.csv
└── figures/
    ├── primary_garch_vs_lstm.png
    └── robustness_garch_vs_lstm.png
```

## Reproducibility and Validation Controls

The implementation includes checks for duplicate dates, missing required values, chronological ordering, target leakage, LSTM feature names, sequence dimensions, target-date alignment and training-only scaling.

The final LSTM results are reported as the mean and sample standard deviation across five fixed random seeds. Earlier results produced before correction of a duplicated `log_return` / missing `squared_return` feature-definition error were discarded and all affected experiments were rerun.

## Generative AI Use

Generative AI use is documented in `docs/ai_use_register.md` and supporting project documentation.

The substantive documented uses were assistance with TGJU methodology documentation, implementation of the OFAC downloader after the collection requirements had been defined, and final dissertation review. Generated material was independently checked against project evidence before being retained.

## Author

Daniel Asghari  
MSc Artificial Intelligence, City St George's, University of London  
2026
