# Machine Learning Methodology & Experimentation

## Base Model Architecture
The system utilizes a hybrid ensemble consisting of three foundational predictors:
1. **Random Forest (RF)**: Robust bagging estimator handling nonlinear tabular interactions.
2. **XGBoost (XGB)**: Gradient-boosted decision trees for tabular feature efficiency.
3. **Feed-Forward Artificial Neural Network (ANN)**: Dense neural architecture capturing high-dimensional embeddings.

## Ensemble Formulation
$$\hat{Y} = w_{RF} \hat{Y}_{RF} + w_{XGB} \hat{Y}_{XGB} + w_{ANN} \hat{Y}_{ANN}$$

Subject to:
$$\sum w_i = 1 \quad \text{and} \quad w_i \ge 0$$

Ensemble weights are optimized via constrained validation loss minimization on held-out validation splits.
