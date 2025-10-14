# frontend/app.py
import streamlit as st
import requests
from typing import List

API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")
st.set_page_config(page_title="Expense Splitter", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

def api_post(path, json=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.post(API_BASE + path, json=json, headers=headers)

def api_get(path):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.get(API_BASE + path, headers=headers)

st.title("Expense Splitter (MVP)")

if not st.session_state.token:
    st.sidebar.header("Auth")
    choice = st.sidebar.selectbox("Action", ["Login", "Register"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    name = st.sidebar.text_input("Name (register only)")
    if choice == "Register":
        if st.sidebar.button("Register"):
            resp = api_post("/auth/register", json={"email": email, "password": password, "name": name})
            if resp.status_code == 200:
                st.success("Registered. Please login.")
            else:
                st.error(resp.text)
    else:
        if st.sidebar.button("Login"):
            # OAuth2 password flow expects form data
            data = {"username": email, "password": password}
            r = requests.post(API_BASE + "/auth/token", data=data)
            if r.status_code == 200:
                token = r.json().get("access_token")
                st.session_state.token = token
                # fetch user
                me = api_get("/users/me")
                if me.status_code == 200:
                    st.session_state.user = me.json()
                st.experimental_rerun()
            else:
                st.error("Login failed: " + r.text)
    st.stop()

# Authenticated UI
st.sidebar.write(f"Logged in as: {st.session_state.user['email']}")
if st.sidebar.button("Logout"):
    st.session_state.token = None
    st.session_state.user = None
    st.experimental_rerun()

# Groups
st.subheader("Groups")
if st.button("Refresh groups"):
    pass
resp = api_get("/groups")
if resp.status_code == 200:
    groups = resp.json()
else:
    st.error("Failed to load groups")
    groups = []

group_names = [g['name'] for g in groups]
group_select = st.selectbox("Select group", options=["Create new..."] + group_names)
if group_select == "Create new...":
    new_name = st.text_input("Group name")
    if st.button("Create group"):
        r = api_post("/groups", json={"name": new_name})
        if r.status_code == 200:
            st.success("Group created")
            st.experimental_rerun()
        else:
            st.error(r.text)
    st.stop()

# find selected group object
group_obj = next((g for g in groups if g['name'] == group_select), None)
if not group_obj:
    st.error("Group not found")
    st.stop()

group_id = group_obj['id']
st.header(f"Group: {group_obj['name']}")

# Show balances
if st.button("Load balances"):
    r = api_get(f"/groups/{group_id}/balances")
    if r.status_code == 200:
        balances = r.json()
        st.table(balances)
    else:
        st.error("Failed to fetch balances")

# Add expense form
st.subheader("Add expense")
# For small MVP, we get members from balances endpoint
r = api_get(f"/groups/{group_id}/balances")
members = []
if r.status_code == 200:
    members = r.json()
member_map = {m['user_id']: f"{m['name'] or m['email']} (id:{m['user_id']})" for m in members}
payer_id = st.selectbox("Payer", options=list(member_map.keys()), format_func=lambda x: member_map.get(x))
amount = st.number_input("Amount", min_value=0.01, format="%.2f")
participants = st.multiselect("Participants", options=list(member_map.keys()), format_func=lambda x: member_map.get(x), default=list(member_map.keys()))
description = st.text_input("Description")
if st.button("Add expense"):
    payload = {"payer_id": payer_id, "amount": amount, "description": description, "participants": participants}
    r = api_post(f"/groups/{group_id}/expenses", json=payload)
    if r.status_code == 200:
        st.success("Expense added")
    else:
        st.error(r.text)

# Settlement
st.subheader("Settlement suggestion")
if st.button("Show settlement plan"):
    r = api_get(f"/groups/{group_id}/settlement")
    if r.status_code == 200:
        plan = r.json()
        st.write(plan)
    else:
        st.error("Failed to fetch settlement")
