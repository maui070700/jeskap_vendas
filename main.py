import streamlit as st
from src.auth import setup_authenticator, handle_login, handle_logout
from src.form import render_form
from PIL import Image


img = Image.open('./static/img/logo.png')
st.set_page_config(page_title='Jeskap', page_icon=img)

st.logo('./static/img/logo2.png')

with open("./static/styles/styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

authenticator = setup_authenticator()

handle_login(authenticator)

if st.session_state.get("authentication_status"):
    render_form()
    handle_logout(authenticator)

elif st.session_state.get("authentication_status") is False:
    st.error('Usuário/Senha inválido')

