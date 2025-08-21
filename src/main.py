import uvicorn
from dotenv import load_dotenv
from api import create_app
import os

# Load environment variables
load_dotenv()

# Check required environment variables
if not os.getenv("GOOGLE_API_KEY"):
    print("❌ ERROR: GOOGLE_API_KEY environment variable is required!")
    print("Please create a .env file with your Google API key:")
    print("GOOGLE_API_KEY=your_api_key_here")
    exit(1)

app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Document Q&A API...")
    print("📚 Backend will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)