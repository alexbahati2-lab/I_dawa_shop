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

# --------------------------------
st.set_page_config(page_title="iDawa AI", layout="wide")
init_db()

# Persistent AI state
if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

# --------------------------------
st.title("🏥 AI Pharmacy App")
st.caption("Fast • Safe • Simple")

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Inventory", "Purchases", "Sales", "Reports"]
)

# --------------------------------
# Main Screen Router
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

# --------------------------------
# 🚀 GLOBAL AI (PERSISTENT)
render_ai_fab()
