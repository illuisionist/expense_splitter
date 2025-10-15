import streamlit as st
from components import api_client, auth_ui, dashboard_tab, expense_tab, settings_tab

# --- Configuration and Session State ---
st.set_page_config(page_title="Expense Splitter", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

st.title("💸 Expense Splitter")

# --- Authentication ---
# This single function call now handles the entire login/register flow
auth_ui.show_auth_form()

# --- Authenticated App UI ---
with st.sidebar:
    st.success(f"Logged in as **{st.session_state.user['email']}**")
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun()

# --- Group Selection and Creation ---
st.header("📂 My Groups")
resp = api_client.api_get("/groups")
if resp.status_code == 200:
    groups = resp.json()
else:
    st.error("Failed to load groups")
    groups = []

group_map = {f"{g['name']} (Owner: {g['owner_name']})": g for g in groups}
group_display_names = list(group_map.keys())
group_select_display = st.selectbox("Select or Create a Group", options=["✨ Create new..."] + group_display_names, label_visibility="collapsed")

if group_select_display == "✨ Create new...":
    with st.form("new_group_form"):
        new_name = st.text_input("Group Name")
        submitted = st.form_submit_button("Create Group")
        if submitted:
            if not new_name:
                st.warning("Group name cannot be empty.")
            else:
                r = api_client.api_post("/groups", json={"name": new_name})
                if r.status_code == 200:
                    st.success("Group created!")
                    st.rerun()
                else:
                    st.error(r.text)
    st.stop()

# --- Main Group View ---
group_obj = group_map.get(group_select_display)
if not group_obj:
    st.info("Please select a group to get started.")
    st.stop()

group_id = group_obj['id']
st.header(f"🏛️ Group: {group_obj['name']}")

# Fetch data needed by multiple tabs
r_members = api_client.api_get(f"/groups/{group_id}/members")
member_map = {}
if r_members.status_code == 200:
    members = r_members.json()
    member_map = {m['id']: f"{m['name'] or m['email']}" for m in members}
else:
    st.error("Failed to load group members.")

# --- Tab-Based Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Add Expense", "👥 Members & Settings"])

with tab1:
    dashboard_tab.show_dashboard(group_id, member_map)

with tab2:
    expense_tab.show_expense_form(group_id, member_map)

with tab3:
    settings_tab.show_settings(group_id, group_obj, member_map)