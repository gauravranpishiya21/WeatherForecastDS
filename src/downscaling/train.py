"""
Script to train the ML downscaling model.

Usage:
    python -m src.downscaling.train --samples 5000 --model-type xgboost
"""
import argparse
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from loguru import logger

from src.downscaling.ml_model import MLDownscaler, generate_synthetic_training_data


def main():
    parser = argparse.ArgumentParser(description="Train ML Downscaling Model")
    parser.add_argument("--samples", type=int, default=5000, help="Number of synthetic samples")
    parser.add_argument("--model-type", type=str, default="xgboost", choices=["rf", "xgboost"],
                        help="Model type: rf (Random Forest) or xgboost")
    parser.add_argument("--csv", type=str, default=None,
                        help="CSV of real training rows (e.g. data/training_real.csv). Overrides synthetic data.")
    parser.add_argument("--save-path", type=str, default="models/downscaler.pkl",
                        help="Path to save trained model")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Hyperlocal Weather Downscaling - ML Training Pipeline")
    logger.info("=" * 60)

    # 1. Load or generate training data
    if args.csv:
        logger.info(f"Step 1/5: Loading real training data from {args.csv}...")
        data = pd.read_csv(args.csv)
        logger.info(f"  Real rows: {len(data)}")
    else:
        logger.info(f"Step 1/5: Generating {args.samples} synthetic training samples...")
        data = generate_synthetic_training_data(n_samples=args.samples)
    logger.info(f"  Dataset shape: {data.shape}")
    logger.info(f"  Features: {list(data.columns[:14])}")

    # 2. Split data into training and testing sets (80/20)
    logger.info("Step 2/5: Splitting data into train/test sets (80/20)...")
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)
    logger.info(f"  Train: {len(train_data)} samples | Test: {len(test_data)} samples")

    # 3. Initialize and train the model
    logger.info(f"Step 3/5: Training {args.model_type.upper()} model...")
    model = MLDownscaler(model_type=args.model_type)
    model.train(train_data)

    # 4. Evaluate model on test set
    logger.info("Step 4/5: Evaluating model on test set...")
    metrics = model.evaluate(test_data)

    logger.info("")
    logger.info("Model Evaluation Metrics:")
    logger.info("-" * 50)
    for var, var_metrics in metrics.items():
        logger.info(f"  {var.upper():>10s}: RMSE={var_metrics['rmse']:.4f} | MAE={var_metrics['mae']:.4f} | R2={var_metrics['r2']:.4f}")
    logger.info("-" * 50)

    # 5. Save the trained model
    save_path = Path(args.save_path)
    if not save_path.is_absolute():
        # Resolve relative to project root
        project_root = Path(__file__).resolve().parent.parent.parent
        save_path = project_root / args.save_path

    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(save_path))
    logger.info(f"Step 5/5: Model saved to {save_path}")
    logger.info("Training pipeline complete!")


if __name__ == "__main__":
    main()
