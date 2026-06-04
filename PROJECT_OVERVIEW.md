# SnapClass — Project Overview

## 1) What this project is
**SnapClass** is a **Streamlit** web application that lets:
- **Teachers** log in and manage subjects/classes, share subject codes, and (in future/placeholder UI) take/manage attendance.
- **Students** log in using **Face Recognition** (and optionally enroll voice for attendance).
- Student profiles and attendance data are persisted in **Supabase**.

The app’s entrypoint is `app.py`, and UI is composed from Streamlit screen functions under `src/screens/`.

---

## 2) Tech stack
### Frontend / UI
- **Python** + **Streamlit**
- Custom UI components under `src/components/`
- Styling via inline CSS injected through `src/ui/base_layout.py`

### Backend / Business logic
- Python functions organized into:
  - `src/database/db.py`: Supabase DB operations + password hashing + student/teacher/subject/attendance CRUD helpers.
  - `src/pipelines/face_pipeline.py`: Face embedding + detection + classifier training + attendance prediction.
  - `src/pipelines/voice_pipeline.py`: Voice embedding generation.

### Database / Auth
- **Supabase** (Postgres + REST interface via Supabase Python client)
- **Teacher login**: username/password stored in Supabase, with passwords hashed using **bcrypt**.
- **Student login**: face recognition by matching stored face embeddings (and optionally voice embeddings).

### ML / Computer Vision dependencies (declared in `requirements.txt`)
- `face-recognition`
- `dlib-bin`
- `scikit-learn`
- `numpy`, `pandas`
- `librosa`
- `resemblyzer`
- `pillow`
- `segno` (likely for QR/code generation in share flow)

---

## 3) Repository structure
Key files/directories:
- `app.py`
- `requirements.txt`
- `src/`
  - `screens/`
    - `home_screen.py`
    - `teacher_screen.py`
    - `student_screen.py`
  - `ui/`
    - `base_layout.py`
  - `components/`
    - UI components like header/footer and subject cards and dialogs.
  - `database/`
    - `config.py` (loads Supabase client from Streamlit secrets)
    - `db.py` (DB + auth + CRUD)
  - `pipelines/`
    - `face_pipeline.py`
    - `voice_pipeline.py`

---

## 4) Application flow (runtime behavior)
### 4.1 Entrypoint (`app.py`)
- Streamlit session state key: `st.session_state['login_type']`
- Router logic:
  - `login_type == 'teacher'` → `teacher_screen()`
  - `login_type == 'student'` → `student_screen()`
  - `login_type is None` → `home_screen()`

### 4.2 Home screen (`src/screens/home_screen.py`)
- Renders headers/footers.
- Displays two buttons:
  - **Student Portal** → sets `st.session_state['login_type']='student'` and reruns.
  - **Teacher Portal** → sets `st.session_state['login_type']='teacher'` and reruns.

### 4.3 Teacher screen (`src/screens/teacher_screen.py`)
- Applies dashboard background + shared base layout styling.
- Branching based on session state:
  - If `teacher_data` exists → show dashboard.
  - Else if `teacher_login_type` indicates login/register → show login or registration UI.

Key teacher dashboard behavior:
- Landing UI has tabs (implemented as buttons) for:
  - **Take Attendance** (currently only shows header placeholder: `teacher_tab_take_attendance()`)
  - **Manage Subjects** (subject list + create subject flow)
  - **Attendance Records** (currently placeholder: `teacher_tab_attendance_records()`)

Manage Subjects tab:
- Uses `teacher_id = st.session_state.teacher_data['teacher_id']`
- Calls `get_teacher_subjects(teacher_id)` to load subjects plus aggregate stats.
- For each subject:
  - Displays a `subject_card(...)` with:
    - total students
    - total classes (computed from unique attendance log timestamps)
  - A “Share Code” button opens `share_subject_dialog(sub['name'], sub['subject_code'])`.

Teacher authentication:
- `teacher_screen_login()` collects username/password.
- `login_teacher()` calls `teacher_login(username, password)`.
- On success, it sets:
  - `st.session_state.user_role = 'teacher'`
  - `st.session_state.teacher_data = teacher`
  - `st.session_state.is_logged_in = True`

Teacher registration:
- `teacher_screen_register()` collects username/name/password.
- `register_teacher()` validates fields, checks uniqueness via `check_teacher_exists()`, hashes password, and inserts teacher record via `create_teacher()`.

### 4.4 Student screen (`src/screens/student_screen.py`)
- Applies dashboard background + base layout styling.
- If `student_data` exists → show `student_dashboard()`.

Student authentication / registration:
- Student login uses **camera input**: `st.camera_input(...)`.
- When a photo is submitted:
  - Image is converted to numpy array.
  - Calls `predict_attendance(img)` from `src/pipelines/face_pipeline.py`.
  - Handles cases:
    - 0 faces → warning
    - >1 faces → warning
    - exactly 1 face:
      - if detected: match student_id, load all students via `get_all_students()`, set `st.session_state.student_data` and rerun.
      - else: show registration UI.

Optional voice enrollment:
- In registration container, includes `st.audio_input(...)`.
- If user creates account:
  - Computes `face_emb` via `get_face_embeddings(img)`.
  - Optionally computes `voice_emb` via `get_voice_embedding(...)`.
  - Inserts new student using `create_student(new_name, face_embedding=..., voice_embedding=...)`.
  - Calls `train_classifier()` after enrollment.

Student dashboard:
- Loads:
  - enrolled subjects via `get_student_subjects(student_id)`
  - attendance logs via `get_student_attendance(student_id)`
- Computes stats per subject (total vs attended).
- Displays each subject using `subject_card(...)`.
- Includes an unenroll button calling `unenroll_student_to_subject(student_id, sid)`.

---

## 5) Database layer details (`src/database/db.py` + `config.py`)
### Supabase client (`src/database/config.py`)
- Creates a Supabase client using Streamlit secrets:
  - `st.secrets["SUPABASE_URL"]`
  - `st.secrets["SUPABASE_KEY"]`

### Password hashing (teachers)
- `hash_pass(pwd)` uses `bcrypt.hashpw(..., gensalt())`.
- `check_pass(pwd, hashed)` checks bcrypt password against stored hash.

### Tables used (inferred from queries)
The code references these Supabase tables:
- `teachers`
  - fields used: `username`, `password`, `name`, and `teacher_id` (implied)
- `students`
  - fields: `student_id` (implied), `name`, `face_embedding`, `voice_embedding`
- `subjects`
  - fields: `subject_code`, `name`, `section`, `teacher_id`
- `subject_students`
  - join table: `student_id`, `subject_id`
- `attendance_logs`
  - fields: `timestamp`, `student_id`, `subject_id`, and `is_present` (implied)

### Key DB functions
- **Teacher**
  - `check_teacher_exists(username)`
  - `create_teacher(username, password, name)`
  - `teacher_login(username, password)`
  - `get_teacher_subjects(teacher_id)`
    - Loads subjects with related aggregates:
      - `subject_students(count)`
      - `attendance_logs(timestamp)`
    - Computes:
      - `total_students`
      - `total_classes` via unique timestamp count
- **Student**
  - `get_all_students()`
  - `create_student(new_name, face_embedding=None, voice_embedding=None)`
  - `get_student_subjects(student_id)`
  - `get_student_attendance(student_id)`
  - `create_attendance(logs)`
- **Enrollment**
  - `enroll_student_to_subject(student_id, subject_id)`
  - `unenroll_student_to_subject(student_id, subject_id)`

---

## 6) ML pipelines
### Face pipeline (`src/pipelines/face_pipeline.py`)
Used by student login and enrollment.
Main call sites observed:
- `predict_attendance(img)`
- `get_face_embeddings(img)`
- `train_classifier()`

Expected responsibilities (based on names + typical flows):
- detect faces in image
- compute embeddings
- compare embeddings to known embeddings
- train/update a classifier for student identities
- predict which student matches the new image

### Voice pipeline (`src/pipelines/voice_pipeline.py`)
Used during student registration.
Observed call:
- `get_voice_embedding(audio_bytes)`

Responsibilities typically include:
- preprocessing audio
- extracting speaker embeddings

---

## 7) Environment / configuration requirements
### Streamlit secrets
`src/database/config.py` requires:
- `SUPABASE_URL`
- `SUPABASE_KEY`

### App run
Run from repo root:
- `streamlit run app.py`

---

## 8) Current limitations / notes
- Teacher “Take Attendance” and “Attendance Records” tabs are mostly placeholders in the current code (they only render headers).
- Database schema is assumed based on Supabase queries; the actual table definitions must match the code.
- Embedding storage types (e.g., arrays) must align with how embeddings are saved in Supabase.

---

## 9) Main entry points (quick index)
- `app.py` → session router
- `src/screens/home_screen.py` → choose teacher/student
- `src/screens/teacher_screen.py` → teacher auth + dashboard
- `src/screens/student_screen.py` → student auth (face) + dashboard
- `src/database/config.py` → Supabase client
- `src/database/db.py` → CRUD + auth + attendance queries
- `src/pipelines/face_pipeline.py` → recognition + training
- `src/pipelines/voice_pipeline.py` → voice embeddings

