import dlib
import numpy as np
import face_recognition_models
from sklearn.svm import SVC
import streamlit as st

from src.database.db import get_all_students


# Load Dlib Models (Cached)

@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()

    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_five_point_model_location()
    )

    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )

    return detector, sp, facerec



# Extract Face Embeddings

def get_face_embeddings(image_np):
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)

    encodings = []

    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))

    return encodings



# Train Classifier (Cached)

@st.cache_resource
def get_trained_model():
    X = []
    y = []

    student_db = get_all_students()

    if not student_db:
        return None

    for student in student_db:
        embedding = student.get("face_embedding")
        student_id = student.get("student_id")

        if embedding is not None and student_id is not None:
            X.append(np.array(embedding))
            y.append(student_id)

    if len(X) == 0:
        return None

    clf = SVC(kernel="linear", probability=True, class_weight="balanced")

    # Handle case where only one class exists
    if len(set(y)) < 2:
        return {"clf": None, "X": X, "y": y}

    clf.fit(X, y)

    return {"clf": clf, "X": X, "y": y}



# Force Retraining

def train_classifier():
    st.cache_resource.clear()
    model_data = get_trained_model()
    return bool(model_data)



# Predict Attendance

def predict_attendance(class_image_np):
    encodings = get_face_embeddings(class_image_np)

    detected_students = {}

    model_data = get_trained_model()

    if not model_data:
        return detected_students, [], len(encodings)

    clf = model_data["clf"]
    X_train = model_data["X"]
    y_train = model_data["y"]

    all_students = sorted(list(set(y_train)))

    for encoding in encodings:

        # If multiple students → use SVM
        if clf is not None:
            predicted_id = int(clf.predict([encoding])[0])
        else:
            # Only one student in DB
            if not all_students:
                continue
            predicted_id = int(all_students[0])

        # Safety check
        if predicted_id not in y_train:
            continue

        student_embedding = X_train[y_train.index(predicted_id)]

        # Euclidean distance
        distance = np.linalg.norm(student_embedding - encoding)

        distance_threshold = 0.6

        if distance <= distance_threshold:
            detected_students[predicted_id] = True

    return detected_students, all_students, len(encodings)