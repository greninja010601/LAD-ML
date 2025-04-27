from testApp.utils.data_preprocessing import prepare_training_data
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor


def train_and_evaluate(course_id, progress_ratio, model_type="xgboost"):
    df = prepare_training_data(course_id, progress_ratio)

    if df.empty:
        print("❌ No data to train.")
        return

    X = df.drop(columns=["student_id", "final_score"])
    y = df["final_score"]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Model selection
    if model_type.lower() == "xgboost":
        model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    elif model_type.lower() == "randomforest":
        model = RandomForestRegressor(n_estimators=100, max_depth=6, random_state=42)
    else:
        raise ValueError("Invalid model_type. Choose 'xgboost' or 'randomforest'.")

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_pred = model.predict(X_test)

    # Metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)

    print(f"📊 Evaluation for Course {course_id} at {int(progress_ratio * 100)}% Progress using {model_type.title()}")
    print(f"R² Score: {r2:.4f}")
    print(f"Mean Absolute Error (MAE): {mae:.2f}")
    print(f"Mean Squared Error (MSE): {mse:.2f}")
    print()

    return {
        "model": model,
        "X_test": X_test,
        "y_test": y_test,
        "y_pred": y_pred,
    }
