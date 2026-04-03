import os
import threading
import requests
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request
from flask_cors import CORS
import pickle
import pandas as pd
import ssl

app = Flask(__name__)
CORS(app)

model = pickle.load(open('model.pkl', 'rb'))

API_KEY = os.getenv("WAQI_API_KEY", "59714bb6dcf89c1e7fbb22fcff7453f4ed2951fc")

# Email configuration from environment variables (safer for cloud deploy)
EMAIL_NOTIFICATIONS = os.getenv("EMAIL_NOTIFICATIONS", "false").lower() in ("1", "true", "yes")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "true").lower() in ("1", "true", "yes")
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
EMAIL_TO = os.getenv("EMAIL_TO", SMTP_USER)


# ✅ AUTO AQI FUNCTION
def get_aqi():
    url = f"https://api.waqi.info/feed/chennai/?token={API_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("AQI API error:", e)
        return 0, 0, 0, 0, 0, 0

    if data.get("status") == "ok":
        iaqi = data["data"].get("iaqi", {})

        pm25 = iaqi.get("pm25", {}).get("v", 0)
        pm10 = iaqi.get("pm10", {}).get("v", 0)
        no2 = iaqi.get("no2", {}).get("v", 0)
        so2 = iaqi.get("so2", {}).get("v", 0)
        co = iaqi.get("co", {}).get("v", 0)
        o3 = iaqi.get("o3", {}).get("v", 0)

        return pm25, pm10, no2, so2, co, o3

    return 0, 0, 0, 0, 0, 0


# ✅ EMAIL ALERT

def _send_email_task(subject, body):
    if not EMAIL_NOTIFICATIONS:
        print("Email notifications are disabled. Skipping send.")
        return

    if not SMTP_USER or not SMTP_PASS or not EMAIL_TO:
        print("Email settings are incomplete; cannot send alert.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10, context=ssl.create_default_context()) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls(context=ssl.create_default_context())
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

        print("✅ Email sent successfully")
    except Exception as e:
        print("Email send failed:", e)


def send_email_alert(aqi_value):
    alert_message = f"🚨 ALERT! AQI Level is {aqi_value}. Hazardous air quality. Stay indoors!"
    thread = threading.Thread(
        target=_send_email_task,
        args=("AQI Hazard Alert", alert_message),
        daemon=True,
    )
    thread.start()


# ✅ HOME ROUTE
@app.route('/')
def home():
    pm25, pm10, no2, so2, co, o3 = get_aqi()

    sample = pd.DataFrame([[pm25, pm10, no2, so2, co, o3]],
    columns=["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"])

    prediction = model.predict(sample)[0]

    alert = None

    if prediction > 300:
        alert = "🚨 Hazardous Air Quality! Stay Indoors!"
        send_email_alert(prediction)
    elif prediction > 200:
        alert = "⚠️ Very Poor Air! Avoid going outside"
    elif prediction > 150:
        alert = "😷 Unhealthy Air! Wear a mask"

    if prediction <= 50:
        category = "Good"
        message = "Safe to go outside"
        color = "green"
    elif prediction <= 100:
        category = "Moderate"
        message = "Be cautious"
        color = "orange"
    elif prediction <= 200:
        category = "Unhealthy"
        message = "Wear mask"
        color = "red"
    elif prediction <= 300:
        category = "Poor"
        message = "Avoid outdoor activities"
        color = "darkred"
    else:
        category = "Hazardous"
        message = "Stay indoors"
        color = "black"

    return render_template('index.html',
                           category=category,
                           message=message,
                           color=color,
                           alert=alert,
                           pm25=pm25,
                           pm10=pm10,
                           no2=no2,
                           so2=so2,
                           co=co,
                           o3=o3,
                           prediction=prediction)


# ✅ MANUAL INPUT ROUTE
@app.route('/predict', methods=['POST'])
def predict():
    pm25 = float(request.form['pm25'])
    pm10 = float(request.form['pm10'])
    no2 = float(request.form['no2'])
    so2 = float(request.form['so2'])
    co = float(request.form['co'])
    o3 = float(request.form['o3'])

    sample = pd.DataFrame([[pm25, pm10, no2, so2, co, o3]],
    columns=["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"])

    prediction = model.predict(sample)[0]

    alert = None

    if prediction > 300:
        alert = "🚨 Hazardous Air Quality! Stay Indoors!"
        send_email_alert(prediction)
    elif prediction > 200:
        alert = "⚠️ Very Poor Air! Avoid going outside"
    elif prediction > 150:
        alert = "😷 Unhealthy Air! Wear a mask"

    if prediction <= 50:
        category = "Good"
        message = "Safe to go outside"
        color = "green"
    elif prediction <= 100:
        category = "Moderate"
        message = "Be cautious"
        color = "orange"
    elif prediction <= 200:
        category = "Unhealthy"
        message = "Wear mask"
        color = "red"
    elif prediction <= 300:
        category = "Poor"
        message = "Avoid outdoor activities"
        color = "darkred"
    else:
        category = "Hazardous"
        message = "Stay indoors"
        color = "black"

    return render_template('index.html',
                           category=category,
                           message=message,
                           color=color,
                           alert=alert,
                           pm25=pm25,
                           pm10=pm10,
                           no2=no2,
                           so2=so2,
                           co=co,
                           o3=o3,
                           prediction=prediction)


# ✅ GRAPH ROUTE
@app.route("/graph")
def graph():
    import plotly.graph_objects as go
    import plotly.express as px

    data = pd.read_csv("cleaned_aqi_dataset.csv")

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=data["AQI"], mode='lines'))
    graph1 = fig1.to_html(full_html=False)

    avg_values = data[["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]].mean()
    fig2 = px.bar(x=avg_values.index, y=avg_values.values)
    graph2 = fig2.to_html(full_html=False)

    fig3 = px.scatter(data, x="PM2.5", y="AQI")
    graph3 = fig3.to_html(full_html=False)

    return render_template("graph.html",
                           graph1=graph1,
                           graph2=graph2,
                           graph3=graph3)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)