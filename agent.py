from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load your API key from .env
load_dotenv()

# Connect to Qwen Cloud
client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"),
    base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

# Clinic information
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
    print("\n Classifying enquiry...")

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
    print(" Drafting personalised reply...")

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
            {
                "role": "system",
                "content": system_prompt
            },
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
    print(" Generating follow-up message...")

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
            {
                "role": "system",
                "content": system_prompt
            },
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


def human_review_checkpoint(classification, reply):
    print("\n" + "=" * 60)
    print(" HUMAN REVIEW REQUIRED")
    print("=" * 60)
    print("Reason: " + str(classification.get("reason", "Standard review")))
    print("Urgency: " + str(classification.get("urgency", "low")).upper())
    print("\nDraft reply for your review:")
    print("-" * 40)
    print(reply)
    print("-" * 40)

    approval = input("\nApprove this reply? (yes/edit/reject): ").strip().lower()

    if approval == "yes":
        print(" Reply approved - sending now.")
        return reply
    elif approval == "edit":
        print("Type your edited reply below. Press Enter twice when done:")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        return "\n".join(lines)
    else:
        print(" Reply rejected - escalating to clinic manager.")
        return None


def run_agent(patient_message):
    print("\n" + "=" * 60)
    print(" CLINICFLOW AGENT - PROCESSING ENQUIRY")
    print("=" * 60)
    print("Patient message received at " + datetime.now().strftime("%H:%M on %d %B %Y"))
    print("Message: " + patient_message)
    print("=" * 60)

    classification = classify_enquiry(patient_message)

    print("\n Classification result:")
    print("   Intent:   " + str(classification.get("intent", "unknown")).upper())
    print("   Urgency:  " + str(classification.get("urgency", "low")).upper())
    print("   Topics:   " + ", ".join(classification.get("topics", [])))

    draft_reply = generate_reply(patient_message, classification)

    final_reply = human_review_checkpoint(classification, draft_reply)

    if final_reply:
        print("\n" + "=" * 60)
        print(" REPLY BEING SENT TO PATIENT:")
        print("=" * 60)
        print(final_reply)

        followup = generate_followup(patient_message, final_reply)

        print("\n" + "=" * 60)
        print(" FOLLOW-UP SCHEDULED (sends in 24hrs if no response):")
        print("=" * 60)
        print(followup)

    print("\n" + "=" * 60)
    print(" AGENT WORKFLOW COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_message = (
        "Hi, I've been having lower back pain for about 3 weeks now. "
        "It's getting worse when I sit for long periods. "
        "Do you have any appointments available this week? "
        "And what would the cost be for an initial assessment?"
    )

    run_agent(test_message)