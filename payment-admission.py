import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import requests
import uuid
import datetime
import os

# --- Authenticator Setup ---
users = {
    'usernames': {
        'janedoe': {
            'name': 'Jane Doe',
            'password': stauth.Hasher(['pass123']).generate()[0]
        },
        'johnsmith': {
            'name': 'John Smith',
            'password': stauth.Hasher(['abc456']).generate()[0]
        }
    }
}

authenticator = stauth.Authenticate(
    users,
    "screening_app",
    "auth",
    cookie_expiry_days=1
)

name, auth_status, username = authenticator.login("Login", "main")

if not auth_status:
    st.warning("Please log in to continue.")
    st.stop()

st.success(f"Welcome {name}!")

# --- Payment Tracking ---
PAYMENT_FILE = "payments.csv"

def has_paid(user):
    if not os.path.exists(PAYMENT_FILE):
        return False
    df = pd.read_csv(PAYMENT_FILE)
    return user in df['username'].values

def save_payment(username):
    df = pd.DataFrame([{'username': username, 'timestamp': datetime.datetime.now()}])
    if os.path.exists(PAYMENT_FILE):
        df_existing = pd.read_csv(PAYMENT_FILE)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_csv(PAYMENT_FILE, index=False)

# --- Paystack Integration ---
paystack_secret_key = "sk_test_85609a6429e8461d30182a74c4c33ae357090e52"
paystack_public_key = "pk_test_d351927aa0cc3bfdefc245a3b51a2ee3ed62e424"

if not has_paid(username):
    st.info("You need to make a ₦50 payment to continue.")
    email = st.text_input("Enter your email for payment:")
    reference = str(uuid.uuid4())

    if st.button("Make Payment (₦50)"):
        pay_url = f"https://paystack.com/pay/lasuscreeningdemo"
import streamlit as st
import pandas as pd
import requests
import uuid
import datetime
import os

# --- Payment Tracking ---
PAYMENT_FILE = "payments.csv"

def has_paid(reference):
    if not os.path.exists(PAYMENT_FILE):
        return False
    df = pd.read_csv(PAYMENT_FILE)
    return reference in df['reference'].values

def save_payment(reference, name):
    df = pd.DataFrame([{'reference': reference, 'name': name, 'timestamp': datetime.datetime.now()}])
    if os.path.exists(PAYMENT_FILE):
        df_existing = pd.read_csv(PAYMENT_FILE)
        df = pd.concat([df_existing, df], ignore_index=True)
    df.to_csv(PAYMENT_FILE, index=False)

# --- Paystack Integration ---
paystack_secret_key = "sk_test_85609a6429e8461d30182a74c4c33ae357090e52"
paystack_public_key = "pk_test_d351927aa0cc3bfdefc245a3b51a2ee3ed62e424"

st.title("LASU Screening Score Calculator")

name_input = st.text_input("Full Name")
jamb_number = st.text_input("JAMB Registration Number")
course = st.text_input("Course of Interest")
email = st.text_input("Email for payment receipt")

st.markdown("---")

reference = str(uuid.uuid4())

if not has_paid(reference):
    st.info("You need to make a ₦50 payment to continue.")
    if st.button("Generate Paystack Payment Link"):
        pay_url = f"https://paystack.com/pay/lasuscreeningdemo"  # Replace with your real pay link
        st.markdown(f"""
            <a href="{pay_url}" target="_blank">
                <button style='background-color:green;color:white;padding:10px;border:none;border-radius:5px;'>
                    Click to Pay ₦50
                </button>
            </a>
        """, unsafe_allow_html=True)
        st.stop()

    verified = st.text_input("Enter your Paystack Reference Code after payment")

    if st.button("Verify Payment"):
        if not verified:
            st.error("Enter the reference code to verify.")
        else:
            headers = {"Authorization": f"Bearer {paystack_secret_key}"}
            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{verified}",
                headers=headers
            )
            res = response.json()
            if res['status'] and res['data']['status'] == 'success':
                st.success("Payment verified successfully.")
                save_payment(verified, name_input)
            else:
                st.error("Payment verification failed. Try again.")
                st.stop()
    else:
        st.stop()

# --- Main Screening App ---
st.header("Enter your JAMB scores (English + 3 other subjects)")
jamb_scores = {}
for i in range(4):
    subject = st.text_input(f"Subject {i+1} Name", key=f"sub_{i}")
    score = st.number_input(f"{subject} Score", 0, 100, key=f"score_{i}")
    jamb_scores[subject] = score

total_jamb = sum(jamb_scores.values())
jamb_percent = total_jamb / 8

if total_jamb < 195:
    st.error(f"Your JAMB score is below the cutoff. Score: {total_jamb}")
    st.stop()

st.header("Enter your WAEC/NECO results for 5 relevant subjects")

grade_to_point = {
    "A1": 10, "B2": 9, "B3": 8,
    "C4": 7, "C5": 6, "C6": 5,
    "D7": 0, "E8": 0, "F9": 0
}

waec_scores = {}
total_waec_points = 0

for i in range(5):
    subject = st.text_input(f"WAEC Subject {i+1}", key=f"waec_sub_{i}")
    grade = st.selectbox(f"{subject} Grade", list(grade_to_point.keys()), key=f"waec_grade_{i}")
    point = grade_to_point[grade]
    waec_scores[subject] = (grade, point)
    total_waec_points += point

aggregate_score = jamb_percent + total_waec_points

st.subheader("📊 Result Summary")
st.write(f"**JAMB Total Score:** {total_jamb}")
st.write(f"**JAMB Screening Score (÷8):** {jamb_percent:.2f}%")
st.write(f"**WAEC/NECO Points:** {total_waec_points}")
st.write(f"**Aggregate Score:** {aggregate_score:.2f}%")

if aggregate_score >= 50:
    st.success(f"🎉 Congratulations, {name_input}, with JAMB No. {jamb_number}, you're qualified to register into Lagos State University with an aggregate score of {aggregate_score:.2f}%.")
else:
    st.error("Sorry, you did not meet the minimum aggregate requirement.")

# --- HTML Download ---
from io import StringIO

if st.button("Generate Printable Report"):
    html = f"""
    <h2>LASU Screening Result</h2>
    <p><b>Name:</b> {name_input}</p>
    <p><b>JAMB Number:</b> {jamb_number}</p>
    <p><b>Course:</b> {course}</p>
    <h4>JAMB Scores</h4>
    <ul>
        {''.join([f"<li>{k}: {v}</li>" for k, v in jamb_scores.items()])}
    </ul>
    <p><b>Total JAMB Score:</b> {total_jamb} (→ {jamb_percent:.2f}%)</p>
    <h4>WAEC/NECO Results</h4>
    <ul>
        {''.join([f"<li>{k}: {v[0]} ({v[1]} points)</li>" for k, v in waec_scores.items()])}
    </ul>
    <p><b>Total WAEC Points:</b> {total_waec_points}</p>
    <p><b>Aggregate Score:</b> {aggregate_score:.2f}%</p>
    <hr>
    <p>{'🎉 You are qualified for admission.' if aggregate_score >= 50 else '❌ You are not qualified for admission.'}</p>
    """

    st.download_button("Download HTML Result", html, file_name="screening_result.html")
