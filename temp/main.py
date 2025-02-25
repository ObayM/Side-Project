from fastapi import FastAPI, HTTPException, BackgroundTasks
from google import genai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from pinecone import Pinecone
import pyttsx3
import threading
from time import sleep
import speech_recognition as sr
from fastapi.middleware.cors import CORSMiddleware
import typing_extensions as typing


load_dotenv()

app = FastAPI()


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# Load environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = "isef-project"
PINECONE_NAME_SPACE = "task-commands"
# Configure GenAI
genai.configure(api_key=GOOGLE_API_KEY)

# Configure Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
pinecone_index = pc.Index(PINECONE_INDEX_NAME)


# Models
class UserQuery(BaseModel):
    query: str

class EmbeddingRequest(BaseModel):
    text: str

class PineconeQuery(BaseModel):
    vector: list
    top_k: int = 5

class PineconeStoreRequest(BaseModel):
    id: str
    vector: list
    metadata: dict = {}

# Routes

system_prompt = """

Respond to user queries in JSON format. Include a message and routing information, selecting one of three specific actions based on the query: 

1. **General Task**  
2. **Explain a Website**  
3. **Explain a Screen**
4. **NULL/Other**

### **Input:**  
A user query (e.g., request, command, or question).

### **Output:**  
A JSON response structured as:  

```json
{
    "Message": "A response to the user query, e.g., 'Okay, I’ll handle this' or 'Here’s the explanation'.",
    "Routing": {
        "Action": "Choose one of: 'General Task', 'Explain a Website', or 'Explain a Screen'.",
        "Details": "Additional context or null if not needed."
    }
}
```

### **Examples:**  

1. **General Task:**  
   ```json
   {
       "Message": "Sure, I’ll handle that for you.",
       "Routing": {
           "Action": "General Task",
           "Details": "Execute the user’s requested task."
       }
   }
   ```

2. **Explain a Website:**  
   ```json
   {
       "Message": "Here’s an explanation of the website.",
       "Routing": {
           "Action": "Explain a Website",
           "Details": "Provide a detailed explanation of the website’s purpose, functionality, or design."
       }
   }
   ```

3. **Explain a Screen:**  
   ```json
   {
       "Message": "Let me explain this screen.",
       "Routing": {
           "Action": "Explain a Screen",
           "Details": "Provide details about the specific screen, its elements, or functionality."
       }
   }
   ```
"""

class RoutingDetails(typing.TypedDict):
    Action: str
    Details: typing.Optional[str]

class RoutingResponse(typing.TypedDict):
    Message: str
    Routing: RoutingDetails

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    system_instruction=system_prompt
)

chat = model.start_chat(history=[])

# Functions
def run_commands(command):
    if command.startswith("```"):
        command = command[3:-3]
        os.system(command)
    elif command.startswith("python"):
        os.system(command)
    else:
        print("Unknown command")
    

def gemini_embed_text(text):
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text
            )
            return result['embedding']
        except Exception as e:
            print(f"Error generating embedding for text: {e}")
            return None


def process_query(query):
    if not query:
        return

    query_embedding = gemini_embed_text(query)

    results = pinecone_index.query(
        vector=query_embedding,
        top_k=5,
        namespace=PINECONE_NAME_SPACE,
        include_metadata=True
    )

    contexts = [item['metadata']['example'] for item in results.to_dict()['matches']]

    message = "<CONTEXT>\n" + "\n\n-------\n\n".join(contexts[:10]) + "\n-------\n</CONTEXT>\n\n\n\nMY QUESTION:\n" + query

    return message
def get_llm_response(msg,system_prompt):

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash",system_instruction=system_prompt)
    response = model.generate_content(msg)
    return response.text

@app.post("/router/")
async def router(query: UserQuery):

    response = chat.send_message(query.query,
        generation_config=genai.GenerationConfig(
        response_mime_type="application/json", response_schema=RoutingResponse
    ))
    return response.text

class CommandRequest(BaseModel):
    command: str

@app.post("/excute/")
async def excute(request :CommandRequest):
    if request.command != "NULL/Other":
        prompt = process_query(request.command)
        response = get_llm_response(prompt,
        """Your solo task is to choose a command also modify the examples uses from the context and match it with the user query  , be smart  get the most of the commands, even use it in abnormal situations, don't add anything else , just the command
    What if there's no command available? after thinking so much of course Just reply with "FINAL PROMPT: {Description of the user query/task}" and don't add anything else.""",
            )
        if "python" in response:
            run_commands(response)
        elif "FINAL PROMPT" in response:
            with open('/temp/prompt.txt', 'w+') as f:
                f.write(response)
            sleep(1)
            os.system("python3 server/services/code_generator.py")
        
    
    return {"Success": True}



@app.post("/pinecone/search/")
async def pinecone_search(request: PineconeQuery):
    """Search in Pinecone index using the provided vector."""
    try:
        results = pinecone_index.query(
            vector=request.vector, top_k=request.top_k, include_metadata=True
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pinecone/store/")
async def pinecone_store(request: PineconeStoreRequest):
    """Store a vector in Pinecone."""
    try:
        pinecone_index.upsert(vectors=[{
            "id": request.id,
            "values": request.vector,
            "metadata": request.metadata
        }])
        return {"message": "Vector stored successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-code/")
async def generate_code(query: UserQuery):
    """Generate Python code for the given query."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction="""
            Generate Python code for the task specified...
            """,
        )
        chat = model.start_chat(history=[])
        response = chat.send_message(query.query)
        return {"code": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


