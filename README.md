# Expense Splitter 💸

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)

A full-stack web application built with a FastAPI backend and a Streamlit frontend that allows users to create groups, track shared expenses, and settle balances. Inspired by popular apps like Splitwise.

## ✨ Features

- ✅ **User Authentication**: Secure user registration and JWT token-based login.
- ✅ **Group Management**: Create groups, add members by email, and delete groups (owner only).
- ✅ **Flexible Expense Splitting**:
  - **Equal Split**: Automatically divide the cost equally among selected participants.
  - **Exact Amounts**: Specify the exact share for each person.
- ✅ **Real-time Balances**: View a clear summary of who owes whom in the group.
- ✅ **Settlement Plan**: Generate a simple plan to see the most efficient way to settle debts.
- ✅ **Record Payments**: Manually record payments between members to clear dues.
- ✅ **Polished UI**: A clean, beautified user interface with tab-based navigation and interactive components.

## 🛠️ Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Uvicorn, SQLite
- **Frontend**: Streamlit
- **Version Control**: Git & GitHub



## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

- Python 3.8+
- Git

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-github-repo-url>
    cd expense-splitter
    ```

2.  **Create `requirements.txt` files:**
    Before setting up, you need to generate `requirements.txt` files so others can easily install the dependencies.
    - **For the backend**, navigate to `backend/` in your terminal and run: `pip freeze > requirements.txt`
    - **For the frontend**, navigate to `frontend/` in your terminal and run: `pip freeze > requirements.txt`
    *(Remember to commit these new files to your GitHub repository!)*

---

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # Create the environment
    python -m venv venv

    # Activate on Windows
    .\venv\Scripts\activate

    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the backend server:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The backend API will be running at `http://127.0.0.1:8000`.

---

### Frontend Setup

1.  **Open a new terminal** and navigate to the frontend directory:
    ```bash
    cd frontend
    ```
    *(If you used a virtual environment for the backend, you can use the same one for the frontend).*

2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Streamlit app:**
    ```bash
    streamlit run app.py
    ```
    The frontend will be running at `http://localhost:8501`. Open this URL in your browser to use the application.

## 📖 API Endpoints

<details>
<summary>Click to view major API endpoints</summary>

- `POST /auth/register`: Create a new user.
- `POST /auth/token`: Log in and receive a JWT token.
- `GET /users/me`: Get details for the current logged-in user.
- `GET /groups`: Get all groups the current user is a member of.
- `POST /groups`: Create a new group.
- `DELETE /groups/{group_id}`: Delete a group.
- `GET /groups/{group_id}/members`: Get all members of a group.
- `POST /groups/{group_id}/members`: Add a new member to a group.
- `POST /groups/{group_id}/expenses`: Add a new expense.
- `GET /groups/{group_id}/balances`: Compute the final balances for a group.
- `GET /groups/{group_id}/settlement`: Generate a settlement plan.
- `POST /groups/{group_id}/settle`: Record a payment between members.

</details>

## 📁 Project Structure
```text
expense-splitter/
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- auth.py
|   |   |-- crud.py
|   |   |-- db.py
|   |   |-- main.py
|   |   |-- models.py
|   |   `-- schemas.py
|   `-- expenses.db  (Note: Should be in .gitignore)
|-- frontend/
|   `-- app.py
|-- .gitignore
`-- README.md