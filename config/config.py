import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

ES_HOST = "https://team3es.ap.loclx.io"
UPSTAGE_API_KEY = os.environ.get('UPSTAGE_API_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

intent_llm = ChatOpenAI(model = 'gpt-4o',
                        api_key = OPENAI_API_KEY,
                        temperature=0.3)