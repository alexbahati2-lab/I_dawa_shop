import streamlit as st
from database import init_db
from inventory import inventory_screen
from purchases import purchases_screen
from sales import (
    quick_sale_screen,
    dosage_sale_screen,
    sales_receipt_screen,
    daily_sales_report
)
from reports import low_stock_report, expiry_report
from ai_assistant import render_ai_fab
from utils.whatsapp_notifier import notify

# ---------------------------
# LOGIN FUNCTION
# ---------------------------
def login_screen():
    st.title("🔐 Idawa Shop Login")

    name = st.text_input("Name")
    password = st.text_input("Password", type="password")

    st.caption("Demo password: 1234")  # password hint

    if st.button("Login"):
        if password == "1234" and name.strip():
            st.session_state.logged_in = True
            st.session_state.username = name

            # 🔔 WhatsApp notify on login
            try:
                notify(name, "Logged into Idawa Shop Demo")
            except Exception:
                pass  # prevent crash if Twilio fails

            st.success(f"Welcome, {name}!")
            st.rerun()
        else:
            st.error("Invalid credentials")


# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="iDawa AI", layout="wide")
init_db()

# ---------------------------
# AUTHENTICATION GATE
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
    st.stop()  # stop execution until login

# ---------------------------
# Persistent AI state
# ---------------------------
if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

# ---------------------------
# SIDEBAR + LOGOUT
# ---------------------------
st.sidebar.write(f"👤 {st.session_state.username}")

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Inventory", "Purchases", "Sales", "Reports"]
)

# ---------------------------
# MAIN SCREEN ROUTER
# ---------------------------
if menu == "Dashboard":
    st.subheader("📊 Dashboard")
    st.info("Welcome to AI Pharmacy App")

elif menu == "Inventory":
    inventory_screen()

elif menu == "Purchases":
    purchases_screen()

elif menu == "Sales":
    option = st.radio(
        "Sales Options",
        ["Quick Sale", "Dosage Sale", "Receipt", "Daily Report"]
    )
    if option == "Quick Sale":
        quick_sale_screen()
    elif option == "Dosage Sale":
        dosage_sale_screen()
    elif option == "Receipt":
        sales_receipt_screen()
    elif option == "Daily Report":
        daily_sales_report()

elif menu == "Reports":
    low_stock_report()
    st.divider()
    expiry_report()

# ---------------------------
# GLOBAL AI (PERSISTENT)
render_ai_fab()
  