import os
import django

# --- Setup Django environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testProject.settings')  # replace 'testProject' with your project name
django.setup()

# --- Now imports ---
import joblib
from sklearn.metrics import r2_score, mean_absolute_error
from data_preprocessing import prepare_combined_training_data

def test_saved_model(model_filename, spring_course_id, fall_course_id, progress_ratio):
    # Step 1: Prepare merged Spring + Fall data
    df = prepare_combined_training_data(spring_course_id, fall_course_id, progress_ratio)

    if df.empty:
        print("⚠️ No data found for testing!")
        return

    # Step 2: Separate features (X) and labels (y)
    X = df.drop(columns=['student_id', 'final_score'])
    y = df['final_score']

    # Step 3: Load the trained model
    model = joblib.load(model_filename)

    # Step 4: Predict
    y_pred = model.predict(X)

    # Step 5: Evaluate
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)

    print(f"\n📈 Evaluation Results for {model_filename}:")
    print(f"R2 Score: {r2:.4f}")     
    print(f"Mean Absolute Error (MAE): {mae:.2f}")

if __name__ == "__main__":
    # 🖊️ Replace with your real course IDs
    spring_course_id = 177318
    fall_course_id = 187540 

    # 🖊️ Testing 20% model
    test_saved_model(model_filename="cs165_combined_model_20.pkl", 
                     spring_course_id=spring_course_id, 
                     fall_course_id=fall_course_id, 
                     progress_ratio=0.2)


