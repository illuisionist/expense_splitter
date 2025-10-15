import streamlit as st
import requests

API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")

def api_post(path, json=None, data=None):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.post(API_BASE + path, json=json, data=data, headers=headers)

def api_get(path):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.get(API_BASE + path, headers=headers)

def api_delete(path):
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.delete(API_BASE + path, headers=headers)