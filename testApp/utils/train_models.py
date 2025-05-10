import joblib
from xgboost import XGBRegressor
from testApp.utils.data_preprocessing import prepare_combined_training_data

def train_and_save_combined_model(spring_course_id, fall_course_id, progress_ratio, output_filename):
    # Step 1: Prepare combined Spring + Fall data
    df = prepare_combined_training_data(spring_course_id, fall_course_id, progress_ratio)

    # Step 2: Check if data is available
    if df.empty:
        print(f"⚠️ No data available for training {output_filename}.")
        return

    # Step 3: Split into X and y
    X = df.drop(columns=['student_id', 'final_score'])
    y = df['final_score']

    # Step 4: Train model
    model = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    model.fit(X, y)

    # Step 5: Save model
    joblib.dump(model, output_filename)
    print(f"✅ Trained and saved combined model to {output_filename}")

if __name__ == "__main__":
    # --- Set your real course IDs here ---
    spring_course_id = 177318 # 🖊️ Replace with your Spring CS165 course_id
    fall_course_id = 187540    # 🖊️ Replace with your Fall CS165 course_id

    # --- Train and save model at 20% course progress ---
    train_and_save_combined_model(spring_course_id, fall_course_id, progress_ratio=0.2, output_filename="cs165_combined_model_20.pkl")

    # --- Train and save model at 50% course progress ---
    train_and_save_combined_model(spring_course_id, fall_course_id, progress_ratio=0.5, output_filename="cs165_combined_model_50.pkl")