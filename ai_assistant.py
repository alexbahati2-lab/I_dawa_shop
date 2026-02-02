# ai_assistant.py
import streamlit as st
from database import get_connection
from datetime import datetime, timedelta
import difflib

NEAR_EXPIRY_DAYS = 30


# ======================================================
# Optional Speech (safe fallback)
# ======================================================
try:
    import speech_recognition as sr
    SPEECH_ENABLED = True
except Exception:
    SPEECH_ENABLED = False


# ======================================================
# Database helpers (single connection usage)
# ======================================================
def get_all_medicine_names(conn):
    cur = conn.cursor()
    cur.execute("SELECT name FROM medicines")
    return [r[0] for r in cur.fetchall()]


def search_medicine(query, conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT name, strength, units_in_stock, expiry_date, batch_no
        FROM medicines
        WHERE name LIKE ? OR batch_no LIKE ?
    """, (f"%{query}%", f"%{query}%"))
    return cur.fetchall()


def expiry_report(conn):
    today = datetime.today().date()
    limit = today + timedelta(days=NEAR_EXPIRY_DAYS)

    cur = conn.cursor()
    cur.execute("""
        SELECT name, expiry_date
        FROM medicines
        WHERE expiry_date IS NOT NULL
    """)

    expiring = []

    for name, expiry in cur.fetchall():
        try:
            exp = datetime.strptime(expiry, "%Y-%m-%d").date()
            if exp <= limit:
                expiring.append((name, expiry))
        except Exception:
            pass

    return expiring


# ======================================================
# AI Logic
# ======================================================
def process_ai_query(query):
    query = query.lower().strip()

    conn = get_connection()

    # expiry questions
    if "expire" in query or "expiry" in query:
        results = expiry_report(conn)
        conn.close()
        return format_expiry(results)

    # normal search
    results = search_medicine(query, conn)

    if results:
        conn.close()
        return format_medicine(results)

    # fuzzy suggestion
    names = get_all_medicine_names(conn)
    conn.close()

    suggestion = difflib.get_close_matches(query, names, n=1, cutoff=0.6)

    if suggestion:
        return f"🤔 Did you mean **{suggestion[0]}** ?"

    return "❌ Drug not found. Try scanning barcode or typing full name."


# ======================================================
# Formatters (clean responses)
# ======================================================
def format_medicine(results):
    msg = "📦 **Medicine Results:**\n\n"

    for n, s, stock, exp, batch in results:
        line = f"**{n} {s}** — Stock: {stock}"
        if exp:
            line += f" | Expiry: {exp}"
        if batch:
            line += f" | Batch: {batch}"
        msg += line + "\n"

    return msg


def format_expiry(results):
    if not results:
        return "✅ No drugs expiring soon."

    msg = "⚠️ **Drugs expiring soon:**\n\n"
    for n, e in results:
        msg += f"- {n} (Expiry: {e})\n"

    return msg


# ======================================================
# Voice (non-blocking safe)
# ======================================================
def listen_voice():
    if not SPEECH_ENABLED:
        return None

    r = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=3)
            return r.recognize_google(audio)
    except Exception:
        return None


# ======================================================
# UI Component
# ======================================================
def render_ai_fab():

    # ---------- styles ----------
    st.markdown("""
    <style>
    .chat-bubble-user {
        background:#e3f2fd;
        padding:10px;
        border-radius:10px;
        margin:5px 0;
    }
    .chat-bubble-bot {
        background:#f1f8e9;
        padding:10px;
        border-radius:10px;
        margin:5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------- state ----------
    if "ai_open" not in st.session_state:
        st.session_state.ai_open = False

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ---------- toggle button ----------
    if st.button("💡 Assistant"):
        st.session_state.ai_open = not st.session_state.ai_open

    if not st.session_state.ai_open:
        return

    st.divider()
    st.subheader("🤖 Pharmacy Assistant")

    mode = st.radio("Input", ["Text", "Voice"], horizontal=True)

    query = ""

    # ---------- TEXT ----------
    if mode == "Text":
        query = st.text_input("Ask something...", key="assistant_input")

        if st.button("Send"):
            handle_query(query)

    # ---------- VOICE ----------
    else:
        if st.button("🎤 Speak"):
            st.info("Listening...")
            spoken = listen_voice()

            if spoken:
                st.success(f"You said: {spoken}")
                handle_query(spoken)
            else:
                st.error("Could not understand speech")


    # ---------- display chat ----------
    for role, msg in st.session_state.chat_history:
        if role == "user":
            st.markdown(f'<div class="chat-bubble-user">🧑 {msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-bot">🤖 {msg}</div>', unsafe_allow_html=True)


# ======================================================
# Chat handler
# ======================================================
def handle_query(query):
    if not query:
        return

    reply = process_ai_query(query)

    st.session_state.chat_history.append(("user", query))
    st.session_state.chat_history.append(("bot", reply))
