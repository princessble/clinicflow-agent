# ClinicFlow Agent — Architecture

## System Overview

Patient → Flask Dashboard → Agent Core → Qwen Cloud API → Human Review → Patient Reply + 24hr Follow-up

## Components

**Patient layer**
Sends enquiry via web form or direct message input

**Flask dashboard (app.py)**
Receives the enquiry, serves the web UI, routes API calls

**Agent core (agent.py)**
Orchestrates the full autonomous workflow

**Classifier**
Calls Qwen Cloud qwen-plus model to detect intent, urgency, and topics

**Reply generator**
Calls Qwen Cloud qwen-plus model to draft a warm personalised reply

**Human review checkpoint**
Presents the draft for one-click approval before sending

**Follow-up scheduler**
Generates and schedules a 24-hour follow-up message automatically

## Deployment

- Backend: Alibaba Cloud ECS instance
- AI models: Qwen Cloud API (qwen-plus)
- Framework: Python Flask
- Frontend: HTML/CSS/JavaScript