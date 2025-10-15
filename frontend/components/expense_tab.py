import streamlit as st
from . import api_client
from decimal import Decimal, ROUND_DOWN

def show_expense_form(group_id, member_map):
    with st.container(border=True):
        if not member_map:
            st.warning("Cannot add expense. No members found in this group.")
            return

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
                    total_shares = sum(st.session_state.shares.values())
                    remaining = float(amount) - total_shares
                    if abs(remaining) > 0.01:
                        st.error("The sum of shares must equal the total amount.")
                    else:
                        shares_payload = [{"user_id": uid, "amount": f"{val:.2f}"} for uid, val in st.session_state.shares.items() if val > 0]
                        is_valid = True
                
                if is_valid:
                    payload = {"payer_id": payer_id, "amount": f"{amount:.2f}", "description": description, "shares": shares_payload}
                    r = api_client.api_post(f"/groups/{group_id}/expenses", json=payload)
                    if r.status_code == 200:
                        st.success("Expense added!")
                        st.session_state.shares = {}
                    else:
                        st.error(f"Failed to add expense: {r.text}")