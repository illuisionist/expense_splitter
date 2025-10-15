import streamlit as st
from . import api_client

def show_dashboard(group_id, member_map):
    st.subheader("📈 Group Balances")
    
    r_balances = api_client.api_get(f"/groups/{group_id}/balances")
    balances_data = []
    if r_balances.status_code == 200:
        balances_data = r_balances.json()
    else:
        st.error("Could not fetch balances.")

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
        with st.container(border=True):
            st.subheader("💡 Settlement Suggestion")
            if st.button("Show Settlement Plan"):
                r = api_client.api_get(f"/groups/{group_id}/settlement")
                if r.status_code == 200:
                    plan = r.json()
                    if plan:
                        st.write(plan)
                    else:
                        st.info("Everyone is settled up!")
                else:
                    st.error("Failed to fetch settlement plan")
    with col2:
        with st.container(border=True):
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
                        r = api_client.api_post(f"/groups/{group_id}/settle", json=payload)
                        if r.status_code == 200:
                            st.success("Settlement recorded!")
                        else:
                            st.error(f"Failed to record settlement: {r.text}")
    
    st.markdown("---")
    
    with st.container(border=True):
        st.subheader("📜 Personal Transaction Log")
        selected_user_id = st.selectbox(
            "Select a member to view their history",
            options=list(member_map.keys()),
            format_func=lambda x: member_map.get(x)
        )
        
        if st.button("Show History"):
            r_history = api_client.api_get(f"/groups/{group_id}/users/{selected_user_id}/history")
            if r_history.status_code == 200:
                history_data = r_history.json()
                if not history_data:
                    st.info(f"{member_map.get(selected_user_id)} has no transactions in this group.")
                else:
                    for item in history_data:
                        col_date, col_desc, col_amt = st.columns([1, 3, 1])
                        with col_date:
                            st.write(item['date'].split('T')[0])
                        with col_desc:
                            st.write(item['description'])
                        with col_amt:
                            if item['amount'] > 0:
                                st.success(f"+ ₹{item['amount']:.2f}")
                            else:
                                st.error(f"- ₹{-item['amount']:.2f}")
            else:
                st.error("Failed to fetch transaction history.")