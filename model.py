import pandas as pd
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# đọc dữ liệu
df = pd.read_csv("dataset.csv")

X = df[["rms","zcr","energy","peak","centroid"]]
y = df["label"]

# chia train/test
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# train
model = LogisticRegression(max_iter=1000)

model.fit(X_train, y_train)

# test
y_pred = model.predict(X_test)

print("Accuracy =", accuracy_score(y_test, y_pred))
print("coef =", model.coef_[0])
print("bias =", model.intercept_[0])

# lưu model
joblib.dump(model, "stone_model.pkl")

print("Model saved: stone_model.pkl")