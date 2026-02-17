import sys
sys.path.append('..')

import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, 
    classification_report,
    roc_auc_score,
    confusion_matrix
)
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# Feature columns - must match what MatchupEngine computes
FEATURE_COLUMNS = [
    "reach_diff",
    "height_diff",
    "striking_output_diff",
    "striking_defense_diff",
    "striking_accuracy_diff",
    "striking_absorbed_diff",
    "takedown_offense_diff",
    "takedown_defense_diff",
    "takedown_accuracy_diff",
    "win_pct_diff",
    "experience_diff"
]

def train_models(data_path='../data/training_data.csv'):
    """Train multiple models and save the best one."""
    
    print("Loading training data...")
    df = pd.read_csv(data_path)
    
    X = df[FEATURE_COLUMNS]
    y = df["label"]
    
    print(f"Training samples: {len(df)}")
    print(f"Class balance: {y.value_counts().to_dict()}")
    
    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Define models to try
    models = {
        "logistic_regression": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=42))
        ]),
        "random_forest": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),  # optional for RF, but fine
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=6,
                min_samples_split=10,
                random_state=42
            ))
        ]),
        "gradient_boosting": Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),  # optional for GB, but fine
            ("clf", GradientBoostingClassifier(
                n_estimators=200,
                learning_rate=0.05,
                max_depth=4,
                subsample=0.8,
                random_state=42
            ))
        ]),
    }

    
    best_model = None
    best_score = 0
    best_name = ""
    results = {}
    
    print("\n--- Training Models ---\n")
    
    for name, pipeline in models.items():
        # Cross validation score
        cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='roc_auc')
        
        # Fit and evaluate
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)
        
        results[name] = {
            "accuracy": accuracy,
            "auc": auc,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std()
        }
        
        print(f"Model: {name}")
        print(f"  Accuracy:  {accuracy:.3f}")
        print(f"  ROC-AUC:   {auc:.3f}")
        print(f"  CV AUC:    {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        print()
        
        if auc > best_score:
            best_score = auc
            best_model = pipeline
            best_name = name
    
    print(f"--- Best Model: {best_name} (AUC: {best_score:.3f}) ---\n")
    
    # Feature importance (for gradient boosting / random forest)
    best_clf = best_model.named_steps['clf']
    if hasattr(best_clf, 'feature_importances_'):
        importances = best_clf.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': FEATURE_COLUMNS,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        print("Feature Importances:")
        for _, row in feature_importance.iterrows():
            bar = '█' * int(row['importance'] * 50)
            print(f"  {row['feature']:<30} {bar} {row['importance']:.3f}")
        print()
    
    # Save the best model
    os.makedirs('../models', exist_ok=True)
    model_path = '../models/fight_predictor.joblib'
    
    joblib.dump({
        'pipeline': best_model,
        'model_name': best_name,
        'feature_columns': FEATURE_COLUMNS,
        'auc_score': best_score,
        'version': 'v2_ml'
    }, model_path)
    
    print(f"✅ Model saved to {model_path}")
    print(f"   Model type: {best_name}")
    print(f"   AUC Score: {best_score:.3f}")
    
    return best_model, results


if __name__ == "__main__":
    train_models()