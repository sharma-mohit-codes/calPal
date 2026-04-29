# CalPal 🗓️🤖  
**AI-Powered Google Calendar Assistant**

CalPal is a GenAI-based calendar assistant that lets users manage their Google Calendar using simple natural language prompts instead of manual clicks.

---

## 🚀 What It Does

Users can type requests like:

- “Schedule a meeting tomorrow at 5 PM”  
- “Show my today's upcoming events”  
- “Delete my 3 PM call”  

CalPal understands the request and performs the action automatically on Google Calendar.

---

## 🧠 Tech Stack

### Frontend
- React (Vite)

### Backend
- Python  
- FastAPI  

### AI Layer
- Groq API  
- LLaMA-3 model (natural language → structured intent)

### Authentication
- Google OAuth  

### Database
- MongoDB  

### Calendar Integration
- Google Calendar API  

---

## ⚙️ Workflow

1. User logs in with Google  
2. User enters a natural language prompt  
3. Groq LLM extracts **intent** and **event title**  
4. Backend NLP layer extracts **date, time, duration**  
5. Google Calendar API executes the action  
6. Confirmation is displayed in chat  

---

## 🎯 Goal

To make calendar management fast, conversational, and accessible using AI.


## 📌 Status

Core features working locally ✅  
Improved prompt understanding & event matching 🔧
Working on listing schedule based on period of days/week/month 📅