import streamlit as st
from database import get_connection
from datetime import datetime, timedelta

def low_stock_report():
    st.subheader("🚨 Low Stock Alerts")

    threshold = st.number_input(
        "Low stock threshold",
        min_value=1,
        value=10
    )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, strength, units_in_stock
    FROM medicines
    WHERE units_in_stock <= ?
    ORDER BY units_in_stock ASC
    """, (threshold,))

    rows = cursor.fetchall()
    conn.close()

    if rows:
        st.error("Low stock medicines detected!")
        st.table(rows)
    else:
        st.success("All stock levels are healthy.")

def expiry_report():
    st.subheader("⏰ Expiry Alerts")

    days = st.selectbox(
        "Show medicines expiring in",
        [30, 60, 90]
    )

    today = datetime.today()
    limit_date = today + timedelta(days=days)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT name, strength, expiry_date, units_in_stock
    FROM medicines
    WHERE expiry_date IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()

    expiring = []
    for name, strength, expiry, stock in rows:
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d")
            if exp_date <= limit_date:
                expiring.append((name, strength, expiry, stock))
        except:
            continue

    if expiring:
        st.warning("Medicines nearing expiry!")
        st.table(expiring)
    else:
        st.success("No medicines near expiry.")
