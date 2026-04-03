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

API_KEY = "59714bb6dcf89c1e7fbb22fcff7453f4ed2951fc"


# ✅ AUTO AQI FUNCTION
def get_aqi():
    url = f"https://api.waqi.info/feed/chennai/?token={API_KEY}"
    
    response = requests.get(url)
    data = response.json()
    
    if data["status"] == "ok":
        iaqi = data["data"]["iaqi"]

        pm25 = iaqi.get("pm25", {}).get("v", 0)
        pm10 = iaqi.get("pm10", {}).get("v", 0)
        no2 = iaqi.get("no2", {}).get("v", 0)
        so2 = iaqi.get("so2", {}).get("v", 0)
        co = iaqi.get("co", {}).get("v", 0)
        o3 = iaqi.get("o3", {}).get("v", 0)

        return pm25, pm10, no2, so2, co, o3
    else:
        return 0, 0, 0, 0, 0, 0


# ✅ EMAIL ALERT
def send_email_alert(aqi_value):
    try:
        sender_email = "janu012006@gmail.com"
        receiver_email = "janu012006@gmail.com"
        password = "ewwutqpdpypfqgcs"

        message = f"🚨 ALERT! AQI Level is {aqi_value}. Hazardous air quality. Stay indoors!"

        msg = MIMEText(message)
        msg["Subject"] = "AQI Hazard Alert"
        msg["From"] = sender_email
        msg["To"] = receiver_email

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("✅ Email sent successfully")
    except Exception as e:
        print("Email error:", e)


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