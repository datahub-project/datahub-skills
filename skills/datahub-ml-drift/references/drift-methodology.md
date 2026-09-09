# ML Drift Detection Methodology

This document outlines the statistical methodologies used by the DataHub ML Drift Sentinel skill to evaluate training-serving skew (data drift) in machine learning features.

## 1. Population Stability Index (PSI)

The Population Stability Index measures the shift in the distribution of a single variable between two different samples (e.g., baseline training data vs. current production data).

**Calculation:**
1. Bin the numeric data into 10 quantiles based on the baseline distribution (or use distinct categories for categorical variables).
2. Calculate the proportion of records in each bin for both Baseline (B) and Current (C).
3. Apply formula: `PSI = Sum( (C - B) * ln(C / B) )`

**Risk Thresholds:**
- **PSI < 0.1**: LOW risk. Negligible distribution shift.
- **0.1 <= PSI < 0.25**: MEDIUM risk. Moderate shift, warrants monitoring.
- **PSI >= 0.25**: HIGH risk. Significant shift, likely impacting model performance. Immediate investigation required.

## 2. Kolmogorov-Smirnov (KS) Test

The KS test is a non-parametric test used to determine if two continuous 1D probability distributions differ significantly.

**Calculation:**
We use `scipy.stats.ks_2samp` to calculate the test statistic (D) and the p-value.
- `H0` (Null Hypothesis): The two samples are drawn from the same underlying continuous distribution.
- `H1` (Alternative): The distributions are not equal.

**Usage:**
- The KS test is exclusively used for **continuous numeric features**.
- A small p-value (e.g., `< 0.05`) rejects the null hypothesis, indicating statistically significant drift.
- This serves as a secondary indicator alongside the magnitude provided by the PSI score.
