import streamlit as st

st.title("בדיקת Streamlit")
st.write("אם אתה רואה את זה, Streamlit עובד!")

st.header("בדיקת נתונים")
st.write("זהו קובץ בדיקה פשוט")

if st.button("לחץ כאן"):
    st.success("הכפתור עובד!")
