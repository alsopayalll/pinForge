#for testing purposes only 
import requests

PROMPT = """You are a Pinterest SEO strategist. Pinterest is a visual search engine,so titles and descriptions must contain natural, searchable keywords.

PRODUCT: 52-Week Saving Challenge Tracker
DETAILS: Printable PDF, pastel theme, instant download
AUDIENCE: beginners who want to start saving money

Write 5 Pin titles, each under 90 characters, with the main keyword first.
Do not invent prices, discounts or claims."""

r = requests.post("http://localhost:11434/api/chat", json={
    "model": "gemma3",
    "messages": [{"role": "user", "content": PROMPT}],
    "stream": False,
})
print(r.json()["message"]["content"])