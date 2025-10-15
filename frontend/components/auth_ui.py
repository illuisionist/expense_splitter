import streamlit as st
from . import api_client

def show_auth_form():
    if not st.session_state.token:
        with st.sidebar:
            st.header("🔐 Auth")
            choice = st.selectbox("Action", ["Login", "Register"])
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if choice == "Register":
                name = st.text_input("Name (register only)")
                if st.button("Register"):
                    resp = api_client.api_post("/auth/register", json={"email": email, "password": password, "name": name})
                    if resp.status_code == 200:
                        st.success("Registered. Please login.")
                    else:
                        st.error(f"Registration failed: {resp.text}")
            else: # Login
                if st.button("Login"):
                    data = {"username": email, "password": password}
                    r = api_client.api_post("/auth/token", data=data)
                    if r.status_code == 200:
                        token = r.json().get("access_token")
                        st.session_state.token = token
                        me = api_client.api_get("/users/me")
                        if me.status_code == 200:
                            st.session_state.user = me.json()
                        st.rerun()
                    else:
                        st.error(f"Login failed: {r.text}")
        st.stop()