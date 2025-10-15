import streamlit as st
from . import api_client

def show_settings(group_id, group_obj, member_map):
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Current Members")
            if member_map:
                for user_id, name in member_map.items():
                    st.write(f"- {name}")
    
    with col2:
        with st.container(border=True):
            with st.form("add_member_form"):
                st.subheader("➕ Add New Member")
                new_member_email = st.text_input("User Email")
                submitted = st.form_submit_button("Add Member")
                if submitted:
                    if not new_member_email:
                        st.warning("Please enter an email address.")
                    else:
                        r = api_client.api_post(f"/groups/{group_id}/members", json={"email": new_member_email})
                        if r.status_code == 200:
                            st.success(f"User {new_member_email} added!")
                        else:
                            st.error(f"Failed to add member: {r.text}")

    st.markdown("---")
    with st.container(border=True):
        st.subheader("🚨 Danger Zone")
        if group_obj['owner_id'] == st.session_state.user['id']:
            with st.expander("Delete Group"):
                st.error("This will permanently delete the group and all its expenses. This action cannot be undone.")
                if st.button("I understand, delete this group permanently"):
                    r = api_client.api_delete(f"/groups/{group_id}")
                    if r.status_code == 200:
                        st.success("Group deleted successfully.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete group: {r.text}")
        else:
            st.info("Only the group owner can delete this group.")