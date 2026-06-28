from flask import Flask, render_template, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

CLINIC_INFO = {
    "name": "Harmony Physiotherapy Clinic",
    "services": {
        "physiotherapy": "60 per session",
        "sports_massage": "50 per session",
        "back_pain_assessment": "75 per session",
        "follow_up": "45 per session"
    },
    "availability": [
        "Monday to Friday: 9am - 6pm",
        "Saturday: 10am - 2pm",
        "Sunday: Closed"
    ],
    "location": "14 Henry Street, Limerick City",
    "phone": "+353 61 000 000",
    "booking_link": "https://harmonyphysio.ie/book"
}


def classify_enquiry(message):
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent classifier for a physiotherapy clinic. "
                    "Analyse the patient message and return a JSON response with: "
                    "intent: one of [pricing, availability, appointment, general, emergency, complaint], "
                    "urgency: one of [low, medium, high], "
                    "topics: list of topics mentioned, "
                    "requires_human: true if complex or sensitive, "
                    "reason: brief explanation. "
                    "Return ONLY valid JSON. No extra text."
                )
            },
            {
                "role": "user",
                "content": "Patient message: " + message
            }
        ],
        temperature=0.1
    )
    raw = response.choices[0].message.content
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def generate_reply(message, classification):
    services_text = "\n".join([
        "- " + k.replace("_", " ").title() + ": " + v
        for k, v in CLINIC_INFO["services"].items()
    ])
    availability_text = "\n".join(CLINIC_INFO["availability"])

    system_prompt = (
        "You are a warm, professional receptionist at "
        + CLINIC_INFO["name"]
        + " in Limerick, Ireland.\n\n"
        "Services and Prices:\n" + services_text + "\n\n"
        "Opening Hours:\n" + availability_text + "\n\n"
        "Location: " + CLINIC_INFO["location"] + "\n"
        "Phone: " + CLINIC_INFO["phone"] + "\n"
        "Online Booking: " + CLINIC_INFO["booking_link"] + "\n\n"
        "Guidelines:\n"
        "- Be warm, empathetic and professional\n"
        "- Address the patient specific concern directly\n"
        "- Mention relevant services and prices naturally\n"
        "- Always offer a clear next step\n"
        "- Keep the reply under 150 words\n"
        "- Never make medical diagnoses\n"
        "- Sign off as: The Team at " + CLINIC_INFO["name"]
    )

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Patient enquiry: " + message
                    + "\nClassification: " + json.dumps(classification)
                    + "\nWrite a personalised reply to this patient."
                )
            }
        ],
        temperature=0.7
    )
    return response.choices[0].message.content


def generate_followup(original_message, original_reply):
    system_prompt = (
        "You are a caring receptionist at " + CLINIC_INFO["name"] + ". "
        "A patient enquired but has not responded to our reply. "
        "Write a brief, warm follow-up message under 80 words. "
        "Be gentle, not pushy. Show genuine care for their wellbeing. "
        "Mention the booking link: " + CLINIC_INFO["booking_link"] + ". "
        "Sign off as: The Team at " + CLINIC_INFO["name"]
    )

    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Original patient message: " + original_message
                    + "\nOur original reply: " + original_reply
                    + "\nWrite a follow-up message to send 24 hours later."
                )
            }
        ],
        temperature=0.7
    )
    return response.choices[0].message.content


@app.route("/")
def index():
    return render_template("index.html", clinic=CLINIC_INFO)


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    message = data.get("message", "")

    classification = classify_enquiry(message)
    reply = generate_reply(message, classification)
    followup = generate_followup(message, reply)

    return jsonify({
        "classification": classification,
        "reply": reply,
        "followup": followup,
        "timestamp": datetime.now().strftime("%H:%M on %d %B %Y")
    })


@app.route("/approve", methods=["POST"])
def approve():
    data = request.get_json()
    action = data.get("action")
    reply = data.get("reply")
    edited_reply = data.get("edited_reply", "")

    if action == "approve":
        return jsonify({"status": "sent", "message": reply})
    elif action == "edit":
        return jsonify({"status": "sent", "message": edited_reply})
    else:
        return jsonify({"status": "rejected", "message": "Escalated to clinic manager"})


if __name__ == "__main__":
    app.run(debug=True)