import streamlit as st
from twilio.rest import Client


def _get_client():
    return Client(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"]
    )


def notify(user, message):
    client = _get_client()
    client.messages.create(
        from_=st.secrets["TWILIO_WHATSAPP_FROM"],
        to=st.secrets["TWILIO_WHATSAPP_TO"],
        body=f"{user}: {message}"
    )
