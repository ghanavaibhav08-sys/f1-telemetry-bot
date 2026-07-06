import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

df = pd.read_csv("state/training_data.csv")
X = df[["practice_score", "quali_score"]]
y = df["actual_finish_position"]

model = LinearRegression()
model.fit(X, y)
joblib.dump(model, "state/predictor_model.joblib")
