import streamlit as st
from database import get_connection
from datetime import datetime, timedelta

LOW_STOCK_THRESHOLD = 10
NEAR_EXPIRY_DAYS = 30


def quick_sale_screen():
    st.subheader("⚡ Quick Sale (OTC)")

    conn = get_connection()
    cursor = conn.cursor()

    # 🔍 Unified scanner / keyboard input
    search = st.text_input(
        "🔍 Scan barcode or type medicine name",
        placeholder="Scan or type here..."
    )

    medicines = []

    if search:
        cursor.execute("""
        SELECT id, name, strength, units_in_stock, sell_price, sale_policy, expiry_date
        FROM medicines
        WHERE
            barcode = ?
            OR name LIKE ?
            OR strength LIKE ?
        ORDER BY name
        """, (
            search,
            f"%{search}%",
            f"%{search}%"
        ))
        medicines = cursor.fetchall()
    else:
        cursor.execute("""
        SELECT id, name, strength, units_in_stock, sell_price, sale_policy, expiry_date
        FROM medicines
        ORDER BY name
        """)
        medicines = cursor.fetchall()

    if not medicines:
        st.warning("❌ Medicine not found.")
        conn.close()
        return

    # ---- AUTO-SELECT LOGIC ----
    med_map = {}
    for mid, name, strength, stock, price, policy, expiry in medicines:
        label = f"{name} {strength} (Stock: {stock})"
        med_map[label] = (mid, stock, price, policy, expiry)

    if len(med_map) == 1:
        selected = list(med_map.keys())[0]
        st.success(f"✔ Selected: {selected}")
    else:
        selected = st.selectbox("Select Medicine", med_map.keys())

    med_id, stock, price, policy, expiry = med_map[selected]

    today = datetime.today().date()

    # ---- EXPIRY LOGIC ----
    expired = False
    near_expiry = False

    if expiry:
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            if exp_date < today:
                expired = True
            elif exp_date <= today + timedelta(days=NEAR_EXPIRY_DAYS):
                near_expiry = True
        except:
            pass

    # ---- WARNINGS ----
    if expired:
        st.error("❌ EXPIRED MEDICINE — SALE BLOCKED")
    elif near_expiry:
        st.warning("⚠️ Near expiry (≤30 days)")

    if stock <= 0:
        st.error("❌ OUT OF STOCK — SALE BLOCKED")
    elif stock <= LOW_STOCK_THRESHOLD:
        st.warning("⚠️ Low stock warning")

    quantity = st.number_input(
        "Quantity (units/ml)",
        min_value=1,
        max_value=stock if stock > 0 else 1,
        disabled=expired or stock <= 0
    )

    total = quantity * price
    st.markdown(f"### 💵 Total: KES {total}")

    if policy == "PRESCRIPTION":
        st.info("ℹ️ Prescription-only medicine. Confirm prescription.")

    can_sell = not expired and stock > 0

    if st.button("✅ SELL", disabled=not can_sell):
        if quantity > stock:
            st.error("Not enough stock.")
        else:
            cursor.execute("""
            INSERT INTO sales (medicine_id, quantity, sale_type, total_price)
            VALUES (?, ?, 'QUICK', ?)
            """, (med_id, quantity, total))

            cursor.execute("""
            UPDATE medicines
            SET units_in_stock = units_in_stock - ?
            WHERE id = ?
            """, (quantity, med_id))

            conn.commit()
            conn.close()
            st.success("Sale completed successfully.")

# ==============================
# 🧪 DOSAGE SALE (PRESCRIPTION)
# ==============================
def dosage_sale_screen():
    st.subheader("🧪 Dosage Sale (Prescription)")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, name, strength, units_in_stock, sell_price, expiry_date
    FROM medicines
    WHERE sale_policy = 'PRESCRIPTION'
    ORDER BY name
    """)
    meds = cursor.fetchall()

    if not meds:
        st.info("No prescription medicines available.")
        conn.close()
        return

    med_map = {}
    for mid, name, strength, stock, price, expiry in meds:
        label = f"{name} {strength} (Stock: {stock})"
        med_map[label] = (mid, stock, price, expiry)

    selected = st.selectbox("Select Medicine", med_map.keys())
    med_id, stock, price, expiry = med_map[selected]

    today = datetime.today().date()
    expired = False
    near_expiry = False

    if expiry:
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            if exp_date < today:
                expired = True
            elif exp_date <= today + timedelta(days=NEAR_EXPIRY_DAYS):
                near_expiry = True
        except:
            pass

    if expired:
        st.error("❌ EXPIRED MEDICINE — SALE BLOCKED")
    elif near_expiry:
        st.warning("⚠️ Near expiry (≤30 days)")

    if stock <= 0:
        st.error("❌ OUT OF STOCK — SALE BLOCKED")
    elif stock <= LOW_STOCK_THRESHOLD:
        st.warning("⚠️ Low stock warning")

    dose = st.number_input("Dose per intake (units/ml)", min_value=1, disabled=expired or stock <= 0)
    frequency = st.number_input("Times per day", min_value=1, disabled=expired or stock <= 0)
    days = st.number_input("Number of days", min_value=1, disabled=expired or stock <= 0)

    total_units = dose * frequency * days
    total_price = total_units * price

    st.markdown(f"### 📦 Total Units: {total_units}")
    st.markdown(f"### 💵 Total Price: KES {total_price}")

    if total_units > stock:
        st.error("Not enough stock available.")

    can_sell = not expired and stock > 0 and total_units <= stock

    if st.button("✅ COMPLETE DOSAGE SALE", disabled=not can_sell):
        cursor.execute("""
        INSERT INTO sales (medicine_id, quantity, sale_type, total_price)
        VALUES (?, ?, 'DOSAGE', ?)
        """, (med_id, total_units, total_price))

        cursor.execute("""
        UPDATE medicines
        SET units_in_stock = units_in_stock - ?
        WHERE id = ?
        """, (total_units, med_id))

        conn.commit()
        conn.close()
        st.success("Dosage sale completed.")


# ==============================
# 🧾 RECEIPT
# ==============================
def sales_receipt_screen():
    st.subheader("🧾 Sales Receipt")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT s.id, m.name, s.quantity, s.sale_type, s.total_price, s.sale_date
    FROM sales s
    JOIN medicines m ON s.medicine_id = m.id
    ORDER BY s.sale_date DESC
    LIMIT 1
    """)

    sale = cursor.fetchone()
    conn.close()

    if not sale:
        st.info("No sales yet.")
        return

    sid, name, qty, stype, total, date = sale

    receipt = f"""
🏥 i_dawa_app RECEIPT
--------------------------
Medicine: {name}
Quantity: {qty}
Sale Type: {stype}
--------------------------
TOTAL: KES {total}
Date: {date}
--------------------------
Thank you!
"""

    st.code(receipt)

    st.download_button(
        "⬇️ Download Receipt",
        receipt,
        file_name=f"receipt_{sid}.txt"
    )


# ==============================
# 📊 DAILY SALES REPORT
# ==============================
def daily_sales_report():
    st.subheader("📊 Daily Sales Report")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DATE(sale_date), COUNT(*), SUM(total_price)
    FROM sales
    GROUP BY DATE(sale_date)
    ORDER BY DATE(sale_date) DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        st.info("No sales records found.")
        return

    st.table({
        "Date": [r[0] for r in rows],
        "Transactions": [r[1] for r in rows],
        "Total Sales (KES)": [r[2] for r in rows]
    })
