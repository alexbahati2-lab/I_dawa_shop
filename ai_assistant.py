import streamlit as st
from database import get_connection
from datetime import datetime, timedelta
import difflib

# -----------------------------
NEAR_EXPIRY_DAYS = 30

# Speech support (optional)
try:
    import speech_recognition as sr
    SPEECH_ENABLED = True
except:
    SPEECH_ENABLED = False

# -----------------------------
def get_all_medicine_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM medicines")
    names = [r[0] for r in cur.fetchall()]
    conn.close()
    return names

# -----------------------------
def search_medicine(query):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT name, strength, units_in_stock, expiry_date, batch_no
        FROM medicines
        WHERE name LIKE ? OR batch_no LIKE ?
    """, (f"%{query}%", f"%{query}%"))

    results = cur.fetchall()
    conn.close()
    return results

# -----------------------------
def expiry_report_ai():
    conn = get_connection()
    cur = conn.cursor()
    today = datetime.today().date()
    limit = today + timedelta(days=NEAR_EXPIRY_DAYS)

    cur.execute("""
        SELECT name, expiry_date FROM medicines
        WHERE expiry_date IS NOT NULL
    """)

    data = []
    for name, expiry in cur.fetchall():
        try:
            exp = datetime.strptime(expiry, "%Y-%m-%d").date()
            if exp <= limit:
                data.append((name, expiry))
        except:
            pass

    conn.close()
    return data

# -----------------------------
def process_ai_query(query):
    query = query.lower().strip()

    if "expire" in query:
        return expiry_report_ai(), "expiry"

    results = search_medicine(query)
    if results:
        return results, "medicine"

    # typo correction
    names = get_all_medicine_names()
    suggestion = difflib.get_close_matches(query, names, n=1, cutoff=0.6)
    if suggestion:
        return suggestion, "suggest"

    return None, "unknown"

# -----------------------------
def listen_voice():
    if not SPEECH_ENABLED:
        return None

    r = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = r.listen(source, timeout=5)
            return r.recognize_google(audio)
        except:
            return None

# -----------------------------
def render_ai_fab():
    # Floating glowing icon
    st.markdown("""
    <style>
    .ai-fab {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: radial-gradient(circle, #ffeb3b, #ff5722);
        width: 80px;
        height: 80px;
        border-radius: 50%;
        font-size: 40px;
        color: white;
        box-shadow: 0 0 20px #ffeb3b;
        text-align: center;
        line-height: 80px;
        cursor: pointer;
        z-index: 9999;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.button("💡", key="ai_fab"):
       st.session_state.ai_open = not st.session_state.ai_open

    if not st.session_state.get("ai_open"):
        return

    st.markdown("---")
    st.subheader("Your AI assistant")

    mode = st.radio("Input Mode", ["Text", "Voice"], horizontal=True)

    query = ""
    if mode == "Text":
        query = st.text_input("Ask something…")

    else:
        if st.button("🎤 Speak"):
            st.info("Listening...")
            spoken = listen_voice()
            if spoken:
                st.success(f"You said: {spoken}")
                query = spoken
            else:
                st.error("Speech not recognized")

    if not query:
        return

    results, kind = process_ai_query(query)

    if kind == "expiry":
        if results:
            st.warning("⚠️ Drugs expiring soon:")
            for n, e in results:
                st.write(f"- {n} (Expiry: {e})")
        else:
            st.success("No drugs expiring soon.")

    elif kind == "medicine":
        for n, s, stock, exp, batch in results:
            msg = f"**{n} {s}** — Stock: {stock}"
            if exp:
                msg += f" | Expiry: {exp}"
            if batch:
                msg += f" | Batch: {batch}"
            st.write(msg)

    elif kind == "suggest":
        st.info(f"Did you mean **{results[0]}** ?")

    else:
        st.info("I couldn’t identify that drug. You can scan or type the barcode.")
