import streamlit as st
from database import get_connection
from datetime import datetime

def purchases_screen():
    st.subheader("📥 Purchases (Stock In)")

    conn = get_connection()
    cur = conn.cursor()

    # --------------------
    # Step 1: Scan / Enter barcode
    # --------------------
    barcode_input = st.text_input("Scan or enter barcode (optional)")

    medicine = None
    if barcode_input:
        cur.execute("SELECT id, name, units_in_stock FROM medicines WHERE barcode = ?", (barcode_input,))
        medicine = cur.fetchone()

    # --------------------
    # Step 2: Fallback manual search
    # --------------------
    if not medicine:
        cur.execute("SELECT id, name FROM medicines ORDER BY name")
        medicines = cur.fetchall()
        if not medicines:
            st.warning("No medicines found. Add medicines first.")
            conn.close()
            return

        med_dict = {name: mid for mid, name in medicines}
        selected_name = st.selectbox("Or select medicine manually", med_dict.keys())
        med_id = med_dict[selected_name]

        cur.execute("SELECT id, name, units_in_stock FROM medicines WHERE id = ?", (med_id,))
        medicine = cur.fetchone()

    med_id, med_name, current_stock = medicine
    st.write(f"Selected Medicine: **{med_name}**")
    st.write(f"Current Stock: {current_stock}")

    # --------------------
    # Step 3: Enter purchase details
    # --------------------
    quantity = st.number_input("Quantity Received (units/ml)", min_value=1)
    buy_price = st.number_input("Buy Price per unit", min_value=0.0)
    expiry_date = st.date_input("Expiry Date")
    supplier = st.text_input("Supplier (optional)")

    # --------------------
    # Step 4: Save purchase
    # --------------------
    if st.button("💾 Save Purchase"):
        cur.execute("""
            INSERT INTO purchases (medicine_id, quantity, buy_price, supplier, expiry_date, purchase_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (med_id, quantity, buy_price, supplier, expiry_date, datetime.now()))

        cur.execute("""
            UPDATE medicines SET units_in_stock = units_in_stock + ? WHERE id = ?
        """, (quantity, med_id))

        conn.commit()
        conn.close()

        st.success(f"Purchase recorded. New stock: {current_stock + quantity}")
