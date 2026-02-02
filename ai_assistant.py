# ai_assistant.py
import streamlit as st
from database import get_connection
from datetime import datetime, timedelta
import difflib
import re

NEAR_EXPIRY_DAYS = 30


# ======================================================
# Optional Speech
# ======================================================
try:
    import speech_recognition as sr
    SPEECH_ENABLED = True
except Exception:
    SPEECH_ENABLED = False


# ======================================================
# ---------------- DATABASE HELPERS --------------------
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
        WHERE LOWER(name) LIKE ? OR LOWER(batch_no) LIKE ?
    """, (f"%{query.lower()}%", f"%{query.lower()}%"))
    return cur.fetchall()


def get_low_stock(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT name, units_in_stock
        FROM medicines
        WHERE units_in_stock < 10
    """)
    return cur.fetchall()


def get_today_sales(conn):
    today = datetime.today().strftime("%Y-%m-%d")
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(total_price)
        FROM sales
        WHERE date LIKE ?
    """, (f"{today}%",))
    total = cur.fetchone()[0] or 0
    return total


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
        except:
            pass

    return expiring


# ======================================================
# --------------- SMART INTENT ENGINE ------------------
# ======================================================
def normalize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text


def detect_intent(query):
    q = normalize(query)

    greetings = ["hello", "hi", "hey"]
    if any(g in q for g in greetings):
        return "greet"

    if "help" in q:
        return "help"

    if "low stock" in q or "running out" in q:
        return "low_stock"

    if "expire" in q:
        return "expiry"

    if "sales today" in q or "today sales" in q:
        return "sales_today"

    if "inventory" in q or "all medicines" in q:
        return "inventory"

    return "medicine"  # default search


# ======================================================
# --------------- RESPONSE FORMATTERS ------------------
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


def format_low_stock(results):
    if not results:
        return "✅ All medicines sufficiently stocked."

    msg = "📉 **Low Stock Medicines:**\n\n"
    for n, stock in results:
        msg += f"- {n} → {stock} left\n"
    return msg


# ======================================================
# ------------------ AI CORE LOGIC ---------------------
# ======================================================
def process_ai_query(query):
    intent = detect_intent(query)

    conn = get_connection()

    # ---------- GREETING ----------
    if intent == "greet":
        conn.close()
        return "Hello 👋 How can I help you today?"

    # ---------- HELP ----------
    if intent == "help":
        conn.close()
        return (
            "You can ask me things like:\n"
            "• hello\n"
            "• low stock\n"
            "• expiry report\n"
            "• today sales\n"
            "• panadol stock\n"
            "• search amoxicillin"
        )

    # ---------- LOW STOCK ----------
    if intent == "low_stock":
        res = get_low_stock(conn)
        conn.close()
        return format_low_stock(res)

    # ---------- EXPIRY ----------
    if intent == "expiry":
        res = expiry_report(conn)
        conn.close()
        return format_expiry(res)

    # ---------- TODAY SALES ----------
    if intent == "sales_today":
        total = get_today_sales(conn)
        conn.close()
        return f"💰 Today's sales total: **KSh {total:,.0f}**"

    # ---------- INVENTORY ----------
    if intent == "inventory":
        names = get_all_medicine_names(conn)
        conn.close()
        return "📋 Inventory:\n\n" + ", ".join(names[:30]) + ("..." if len(names) > 30 else "")

    # ---------- MEDICINE SEARCH ----------
    results = search_medicine(query, conn)

    if results:
        conn.close()
        return format_medicine(results)

    # ---------- SUGGEST ----------
    names = get_all_medicine_names(conn)
    conn.close()

    suggestion = difflib.get_close_matches(query, names, n=1, cutoff=0.5)
    if suggestion:
        return f"🤔 Did you mean **{suggestion[0]}** ?"

    return "❌ Drug not found. Try typing full name or say 'help'."


# ======================================================
# ------------------ VOICE SUPPORT ---------------------
# ======================================================
def listen_voice():
    if not SPEECH_ENABLED:
        return None

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=3)
            return r.recognize_google(audio)
    except:
        return None


# ======================================================
# --------------------- UI -----------------------------
# ======================================================
def render_ai_fab():

    if "ai_open" not in st.session_state:
        st.session_state.ai_open = False

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if st.button("💡 Assistant"):
        st.session_state.ai_open = not st.session_state.ai_open

    if not st.session_state.ai_open:
        return

    st.divider()
    st.subheader("🤖 Pharmacy Assistant")

    conn = get_connection()
    names = get_all_medicine_names(conn)
    conn.close()

    # ---------- AUTOSUGGEST DROPDOWN ----------
    query = st.selectbox(
        "Ask something or pick a medicine",
        [""] + names,
        index=0
    )

    manual = st.text_input("Or type naturally (e.g. 'how many panadol left')")

    final_query = manual if manual else query

    if st.button("Send"):
        handle_query(final_query)

    # ---------- CHAT HISTORY ----------
    for role, msg in st.session_state.chat_history:
        icon = "🧑" if role == "user" else "🤖"
        st.write(f"{icon} {msg}")


# ======================================================
# ----------------- CHAT HANDLER -----------------------
# ======================================================
def handle_query(query):
    if not query:
        return

    reply = process_ai_query(query)

    st.session_state.chat_history.append(("user", query))
    st.session_state.chat_history.append(("bot", reply))
