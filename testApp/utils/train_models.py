import joblib
from xgboost import XGBRegressor
from testApp.utils.data_preprocessing import prepare_training_data

def train_and_save_model(course_id, progress_ratio, output_filename):
    df = prepare_training_data(course_id, progress_ratio)

    if df.empty:
        print(f"⚠️ No data available for training {output_filename}.")
        return

    # Drop student_id and get features/labels
    X = df.drop(columns=['student_id', 'final_score'])
    y = df['final_score']

    # Train model
    model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(X, y)

    # Save model
    joblib.dump(model, output_filename)
    print(f"✅ Trained and saved model to {output_filename}")


if __name__ == "__main__":
    # Train for CS165
    train_and_save_model(course_id=187540, progress_ratio=0.2, output_filename="cs165_model_20.pkl")
    train_and_save_model(course_id=187540, progress_ratio=0.5, output_filename="cs165_model_50.pkl")