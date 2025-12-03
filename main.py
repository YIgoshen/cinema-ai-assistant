from fastapi import FastAPI
from typing import Any, Dict, List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(root_path="/api/v1")

app.add_middleware(
  CORSMiddleware,
  allow_origins=["http://localhost:3000"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

data: List[Dict[str, str]] = [
    # {"title": "What is the n1 movie?", "role": "user"},
    # {"title": "Harry Potter!", "role": "assistant"}
]

@app.get("/")
async def root():
    return {"message": "Hello FaRM app"}

@app.get("/messages")
async def read_messages():
    return data

# -------------------------
# Langchain Setup
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URI = os.getenv('OPENAI_BASE_URI')

# Initialize LLM
llm = ChatOpenAI(
  model='gpt-4o-mini',
  api_key=OPENAI_API_KEY,
  temperature=0.8,
  base_url=OPENAI_BASE_URI,
  max_tokens=400
)

# Memory to keep conversation history
memory = ConversationBufferMemory(return_messages=True)


# Prompt template with conversation history
prompt = ChatPromptTemplate.from_messages([
  ("system", "You are a helpful AI assistant that answers questions about movies."),
  MessagesPlaceholder(variable_name="chat_history"),
  ("human", "{input}"),
])

# Create conversation chain
conversation = prompt | llm

# Pydantic model for request body (recommended)
class MessageRequest(BaseModel):
  title: str


@app.post("/messages")
async def create_message(request: MessageRequest):
    user_input = request.title.strip()
    
    if not user_input:
      return {"error": "Message cannot be empty"}, 400

    # 1. Add user message to history and UI
    data.append({"title": user_input, "role": "user"})

    # 2. Load previous chat history from memory
    chat_history = memory.load_memory_variables({})["history"]

    # 3. Get AI response
    try:
      response = conversation.invoke({
        "input": user_input,
        "chat_history": chat_history
      })
      ai_message = response.content

      # 4. Save both user message and AI response to memory
      memory.save_context(
        {"input": user_input},
        {"output": ai_message}
      )

      # 5. Add AI response to the UI data
      data.append({"title": ai_message, "role": "assistant"})

      print("---------data:::", data)

      # 6. Return only the AI response (or full data if you prefer)
      return {"title": ai_message, "role": "assistant"}

    except Exception as e:
      return {"error": str(e)}, 500
