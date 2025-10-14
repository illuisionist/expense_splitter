# frontend/app.py
import streamlit as st
import requests
from typing import List
from decimal import Decimal, ROUND_DOWN

# --- Configuration and Session State ---
API_BASE = st.secrets.get("API_BASE", "http://127.0.0.1:8000")
st.set_page_config(page_title="Expense Splitter", layout="wide")

if "token" not in st.session_state:
    st.session_state.token = None
if "user" not in st.session_state:
    st.session_state.user = None

# --- API Helper Functions ---
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

st.title("💸 Expense Splitter")

# --- Authentication Section ---
if not st.session_state.token:
    with st.sidebar:
        st.header("🔐 Auth")
        choice = st.selectbox("Action", ["Login", "Register"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if choice == "Register":
            name = st.text_input("Name (register only)")
            if st.button("Register"):
                resp = api_post("/auth/register", json={"email": email, "password": password, "name": name})
                if resp.status_code == 200:
                    st.success("Registered. Please login.")
                else:
                    st.error(f"Registration failed: {resp.text}")
        else: # Login
            if st.button("Login"):
                data = {"username": email, "password": password}
                r = api_post("/auth/token", data=data)
                if r.status_code == 200:
                    token = r.json().get("access_token")
                    st.session_state.token = token
                    me = api_get("/users/me")
                    if me.status_code == 200:
                        st.session_state.user = me.json()
                    st.rerun() # Use modern rerun
                else:
                    st.error(f"Login failed: {r.text}")
    st.stop()


# --- Authenticated App UI ---
with st.sidebar:
    st.success(f"Logged in as **{st.session_state.user['email']}**")
    if st.button("Logout"):
        st.session_state.token = None
        st.session_state.user = None
        st.rerun() # Use modern rerun

# --- Group Selection and Creation ---
st.header("📂 My Groups")

resp = api_get("/groups")
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
                r = api_post("/groups", json={"name": new_name})
                if r.status_code == 200:
                    st.success("Group created!")
                    st.rerun() # Use modern rerun
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

# --- Get Group Members (used in multiple places now) ---
r_members = api_get(f"/groups/{group_id}/members")
member_map = {}
if r_members.status_code == 200:
    members = r_members.json()
    member_map = {m['id']: f"{m['name'] or m['email']}" for m in members}
else:
    st.error("Failed to load group members.")

# --- Tab-Based Layout ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "➕ Add Expense", "👥 Members & Settings"])

with tab1:
    st.subheader("📈 Group Balances")
    
    # Fetch balances
    r_balances = api_get(f"/groups/{group_id}/balances")
    balances_data = []
    if r_balances.status_code == 200:
        balances_data = r_balances.json()
    else:
        st.error("Could not fetch balances.")

    # Show personal balance metric
    my_balance = 0.0
    for b in balances_data:
        if b['user_id'] == st.session_state.user['id']:
            my_balance = b['balance']
            break
    
    if my_balance >= 0:
        st.metric(label="Your Balance", value=f"₹{my_balance:.2f}", delta="You are owed money")
    else:
        st.metric(label="Your Balance", value=f"₹{my_balance:.2f}", delta="You owe money", delta_color="inverse")

    if balances_data:
        st.table(balances_data)
    else:
        st.info("No expenses yet. Add one in the 'Add Expense' tab!")

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True): # Re-enable border
            st.subheader("💡 Settlement Suggestion")
            if st.button("Show Settlement Plan"):
                r = api_get(f"/groups/{group_id}/settlement")
                if r.status_code == 200:
                    plan = r.json()
                    if plan:
                        st.write(plan)
                    else:
                        st.info("Everyone is settled up!")
                else:
                    st.error("Failed to fetch settlement plan")
    with col2:
        with st.container(border=True): # Re-enable border
            with st.form("settlement_form"):
                st.subheader("💸 Record a Payment")
                from_user_id = st.session_state.user['id']
                st.write(f"You ({member_map.get(from_user_id, 'Unknown')}) paid:")
                other_members = {uid: name for uid, name in member_map.items() if uid != from_user_id}
                to_user_id = st.selectbox("To", options=list(other_members.keys()), format_func=lambda x: other_members.get(x))
                settle_amount = st.number_input("Amount", min_value=0.01, value=5.00, format="%.2f")
                submitted = st.form_submit_button("Record Payment")
                if submitted:
                    if not to_user_id:
                        st.warning("Please select a person to pay.")
                    else:
                        payload = {"from_user_id": from_user_id, "to_user_id": to_user_id, "amount": f"{settle_amount:.2f}"}
                        r = api_post(f"/groups/{group_id}/settle", json=payload)
                        if r.status_code == 200:
                            st.success("Settlement recorded!")
                        else:
                            st.error(f"Failed to record settlement: {r.text}")

with tab2:
    with st.container(border=True): # Re-enable border
        if not member_map:
            st.warning("Cannot add expense. No members found in this group.")
            st.stop()

        with st.form("expense_form"):
            st.subheader("📝 Add a New Expense")
            payer_id = st.selectbox("Payer", options=list(member_map.keys()), format_func=lambda x: member_map.get(x))
            amount = st.number_input("Total Amount", min_value=0.01, value=10.00, format="%.2f")
            description = st.text_input("Description (e.g., Dinner, Groceries)")
            
            st.markdown("---")
            split_method = st.radio("How to split?", ["Equally", "By Exact Amounts"], horizontal=True)

            if split_method == "Equally":
                st.write("**Select who participated:**")
                equal_split_participants = st.multiselect("Participants", options=list(member_map.keys()), format_func=lambda x: member_map.get(x), default=list(member_map.keys()))
            else: # By Exact Amounts
                st.write("**Enter share for each participant:**")
                if 'shares' not in st.session_state:
                    st.session_state.shares = {}
                
                for user_id, name in member_map.items():
                    st.session_state.shares[user_id] = st.number_input(f"Share for {name}", min_value=0.00, value=st.session_state.shares.get(user_id, 0.0), format="%.2f", key=f"share_{user_id}_{group_id}")
                
                total_shares = sum(st.session_state.shares.values())
                remaining = float(amount) - total_shares
                
                if abs(remaining) < 0.01:
                    st.success(f"✅ Total shares match the amount: {total_shares:.2f}")
                else:
                    st.warning(f"⚠️ Total shares: {total_shares:.2f}. Remaining: {remaining:.2f}")

            submitted = st.form_submit_button("Add Expense")
            if submitted:
                shares_payload = []
                is_valid = False
                if split_method == "Equally":
                    n = len(equal_split_participants)
                    if n == 0:
                        st.error("You must select at least one participant for an equal split.")
                    else:
                        amount_dec = Decimal(f"{amount:.2f}")
                        n_dec = Decimal(n)
                        base_share = (amount_dec / n_dec).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
                        remainder = amount_dec - (base_share * n)
                        for i, user_id in enumerate(equal_split_participants):
                            share_amount = base_share
                            if i == 0:
                                share_amount += remainder
                            shares_payload.append({"user_id": user_id, "amount": f"{share_amount:.2f}"})
                        is_valid = True
                else: # By Exact Amounts
                    if abs(remaining) > 0.01:
                        st.error("The sum of shares must equal the total amount.")
                    else:
                        shares_payload = [{"user_id": uid, "amount": f"{val:.2f}"} for uid, val in st.session_state.shares.items() if val > 0]
                        is_valid = True
                
                if is_valid:
                    payload = {"payer_id": payer_id, "amount": f"{amount:.2f}", "description": description, "shares": shares_payload}
                    r = api_post(f"/groups/{group_id}/expenses", json=payload)
                    if r.status_code == 200:
                        st.success("Expense added!")
                        st.session_state.shares = {}
                    else:
                        st.error(f"Failed to add expense: {r.text}")

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True): # Re-enable border
            st.subheader("Current Members")
            if member_map:
                for user_id, name in member_map.items():
                    st.write(f"- {name}")
    
    with col2:
        with st.container(border=True): # Re-enable border
            with st.form("add_member_form"):
                st.subheader("➕ Add New Member")
                new_member_email = st.text_input("User Email")
                submitted = st.form_submit_button("Add Member")
                if submitted:
                    if not new_member_email:
                        st.warning("Please enter an email address.")
                    else:
                        r = api_post(f"/groups/{group_id}/members", json={"email": new_member_email})
                        if r.status_code == 200:
                            st.success(f"User {new_member_email} added!")
                        else:
                            st.error(f"Failed to add member: {r.text}")

    st.markdown("---")
    with st.container(border=True): # Re-enable border
        st.subheader("🚨 Danger Zone")
        if group_obj['owner_id'] == st.session_state.user['id']:
            with st.expander("Delete Group"):
                st.error("This will permanently delete the group and all its expenses. This action cannot be undone.")
                if st.button("I understand, delete this group permanently"):
                    r = api_delete(f"/groups/{group_id}")
                    if r.status_code == 200:
                        st.success("Group deleted successfully.")
                        st.rerun() # Use modern rerun
                    else:
                        st.error(f"Failed to delete group: {r.text}")
        else:
            st.info("Only the group owner can delete this group.")