import streamlit as st
from database import get_connection


def inventory_screen():
    st.subheader("📦 Medicine Inventory")

    tabs = st.tabs(["➕ Add Medicine", "📋 View Inventory"])

    # ============================
    # ➕ ADD MEDICINE TAB
    # ============================
    with tabs[0]:
        st.markdown("### Add New Medicine")

        # 🔍 Barcode (scanner or keyboard)
        barcode = st.text_input(
            "🔍 Scan or Enter Barcode (optional)",
            placeholder="Scan barcode or type manually"
        )

        name = st.text_input("Medicine Name")
        batch_no = st.text_input("Batch Number")
        strength = st.text_input("Strength (e.g. 500mg)")
        form = st.selectbox("Form", ["Tablet", "Capsule", "Syrup", "Injection", "Other"])
        unit_type = st.selectbox("Unit Type", ["tablet", "capsule", "ml", "vial"])
        units_per_pack = st.number_input("Units per Pack (optional)", min_value=1)
        expiry_date = st.date_input("Expiry Date")
        buy_price = st.number_input("Buying Price (per unit)", min_value=0.0)
        sell_price = st.number_input("Selling Price (per unit)", min_value=0.0)
        sale_policy = st.selectbox(
            "Sale Policy",
            ["OTC", "ADVICE", "PRESCRIPTION"]
        )

        if st.button("💾 Save Medicine"):
            if not name:
                st.error("Medicine name is required")
            else:
                conn = get_connection()
                cursor = conn.cursor()

                # ⚠️ Optional: warn if barcode already exists
                if barcode:
                    cursor.execute(
                        "SELECT id FROM medicines WHERE barcode = ?",
                        (barcode,)
                    )
                    if cursor.fetchone():
                        st.warning("⚠️ This barcode already exists in inventory.")

                cursor.execute("""
                INSERT INTO medicines
                (barcode, name, batch_no, strength, form, unit_type,
                 units_per_pack, units_in_stock, expiry_date,
                 buy_price, sell_price, sale_policy)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
                """, (
                    barcode if barcode else None,
                    name, batch_no, strength, form, unit_type,
                    units_per_pack, expiry_date,
                    buy_price, sell_price, sale_policy
                ))

                conn.commit()
                conn.close()

                st.success("✅ Medicine added successfully")

    # ============================
    # 📋 VIEW INVENTORY TAB
    # ============================
    with tabs[1]:
        st.markdown("### Current Stock")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT barcode, name, strength, form, unit_type,
               units_in_stock, expiry_date, sell_price, sale_policy
        FROM medicines
        ORDER BY name
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            st.info("No medicines in inventory.")
            return

        for row in rows:
            barcode, name, strength, form, unit_type, stock, expiry, price, policy = row

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])

            with col1:
                st.markdown(f"**{name} {strength}**")
                st.caption(f"{form} • {unit_type}")

            with col2:
                if barcode:
                    st.caption("Barcode")
                    st.code(barcode)
                else:
                    st.caption("No barcode")

            with col3:
                st.write(f"Stock: **{stock}**")

            with col4:
                st.write(f"Expiry: {expiry}")

            with col5:
                st.write(f"KES {price}")
                st.caption(policy)

            st.divider()
