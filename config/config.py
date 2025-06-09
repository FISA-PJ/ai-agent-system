import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

load_dotenv()

UPSTAGE_API_KEY = os.environ.get('UPSTAGE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

agent_llm = ChatOpenAI(model = 'gpt-4o',
                        api_key = OPENAI_API_KEY,
                        temperature=0.3)

intent_llm = ChatOllama(
    model='gemma:2b-instruct',
    temperature=0.3,
    base_url="http://localhost:11434"
)