from dotenv import load_dotenv
from google import genai

# Load GEMINI_API_KEY from .env
load_dotenv()

# Create Gemini client
client = genai.Client()

# Send a test request
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="Reply with exactly: Gemini is working!"
)

print(response.text)