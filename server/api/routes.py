from fastapi import APIRouter, HTTPException
from api.utils import process_query, run_commands, get_llm_response
from api.config import settings
from api.models import UserQuery, CommandRequest, PineconeQuery, PineconeStoreRequest, RoutingDetails
from api.pinecone_utils import pinecone_index
import google.generativeai as genai_old
from google.ai.generativelanguage_v1beta.types import content

import os
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import difflib
import json
from google import genai
import re


router = APIRouter()

# Global file server instance
file_server = None

class FileServer:
    def __init__(self, directory=None, port=8000, api_key=None):
        """Initialize the file server with specified directory and port."""
        self.directory = os.path.abspath(directory) if directory else os.getcwd()
        self.port = port
        self.server = None
        self.server_thread = None
        self.ip_address = self.get_local_ip()
        self.api_key = api_key
        
        # Initialize Gemini client if API key is provided
        if self.api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.api_key)
                self.gemini_enabled = True
                print("Gemini AI search enabled")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
                self.gemini_enabled = False
        else:
            self.gemini_enabled = False
            
    def get_local_ip(self):
        """Get the local IP address of the machine."""
        try:
            # Create a socket to determine the local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # Fallback to localhost if unable to determine IP

    def start_server(self):
        """Start the HTTP server in a separate thread."""
        os.chdir(self.directory)
        
        # Create and configure the HTTP server
        handler = SimpleHTTPRequestHandler
        self.server = HTTPServer(("0.0.0.0", self.port), handler)
        
        # Start the server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(1)
        print(f"Server started at http://{self.ip_address}:{self.port}")
        return True
        
    def stop_server(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            print("Server stopped.")
    
    def interpret_query_with_gemini(self, natural_query):
        """Use Gemini to interpret a natural language query into search parameters."""
        if not self.gemini_enabled:
            print("Gemini AI not enabled. Using direct search.")
            return {"query": natural_query, "directory": self.directory}
            
        try:
            prompt = f"""
            Given this natural language request to find a file: "{natural_query}"
            Extract the following information:
            1. The file name or keywords to search for
            2. Any specific directory mentioned (if none, return "default")
            
            Format your response as a JSON object with the following structure:
            {{
                "query": "search keywords",
                "directory": "specific directory or 'default'"
            }}
            Only return the JSON, without any explanation.
            """
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            
            # Extract the JSON response
            response_text = response.text
            
            # Try to clean and parse the JSON string
            try:
                # Remove any code block markers that might be in the response
                json_str = re.sub(r'```json|```|\n', '', response_text).strip()
                
                # Use Python's eval to convert the string to a dictionary
                # This is safer than using eval() directly on unknown input
                import ast
                result = ast.literal_eval(json_str)
                
                # If directory is 'default', use the current directory
                if result.get('directory') == 'default':
                    result['directory'] = self.directory
                else:
                    # Handle special cases like "desktop"
                    directory = result.get('directory')
                    if directory.lower() == 'desktop':
                        # Get the user's desktop directory
                        home = os.path.expanduser("~")
                        desktop = os.path.join(home, 'Desktop')
                        if os.path.exists(desktop):
                            result['directory'] = desktop
                    elif not os.path.isabs(directory):
                        # If it's a relative path, make it absolute
                        result['directory'] = os.path.abspath(directory)
                        
                return result
            except:
                # Fallback to basic parsing if JSON parsing fails
                if "file name" in response_text.lower() and ":" in response_text:
                    keywords = response_text.split(":")[-1].strip()
                    return {"query": keywords, "directory": self.directory}
                else:
                    return {"query": natural_query, "directory": self.directory}
                    
        except Exception as e:
            print(f"Error using Gemini API: {e}")
            return {"query": natural_query, "directory": self.directory}
    
    def find_files(self, query, directory=None, max_results=5):
        """Find files with names similar to the query."""
        search_dir = directory if directory else self.directory
        all_files = []
        
        # Walk through the directory and collect all files
        for root, _, files in os.walk(search_dir):
            for file in files:
                # Calculate relative path for URL generation
                rel_path = os.path.join(root, file)
                all_files.append(rel_path)
        
        # Find the closest matches
        if not all_files:
            return []
            
        # Try fuzzy matching first
        matches = difflib.get_close_matches(query, all_files, n=max_results, cutoff=0.1)
        
        # If no matches found with difflib, try a more lenient substring search
        if not matches:
            matches = [f for f in all_files if query.lower() in os.path.basename(f).lower()][:max_results]
            
            # If still no matches, try with partial keywords
            if not matches:
                keywords = query.lower().split()
                matches = [f for f in all_files if any(keyword in os.path.basename(f).lower() for keyword in keywords)][:max_results]
                
        return matches
    
    def generate_download_links(self, files):
        """Generate download links for the matched files."""
        links = []
        base_url = f"http://{self.ip_address}:{self.port}"
        
        for file_path in files:
            # Get the relative path for URL generation
            rel_path = os.path.relpath(file_path, self.directory)
            
            # URL encode the file path for proper URL formatting
            url_path = "/".join([part.replace(" ", "%20") for part in rel_path.split(os.sep)])
            link = f"{base_url}/{url_path}"
            
            # Get file metadata
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_size_formatted = format_file_size(file_size)
            
            links.append({
                "name": file_name,
                "path": file_path,
                "size": file_size_formatted,
                "url": link
            })
            
        return links

def format_file_size(size_bytes):
    """Format file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

# Initialize the file server with environment variables
def initialize_file_server(directory=None, port=8000, api_key=None):
    global file_server
    
    # Use environment variables if available
    directory = directory or os.environ.get("FILE_SERVER_DIR", os.getcwd())
    port = port or int(os.environ.get("FILE_SERVER_PORT", 7056))
    api_key = api_key or os.environ.get("GEMINI_API_KEY", None)
    
    file_server = FileServer(directory=directory, port=port, api_key=api_key)
    file_server.start_server()
    return file_server



# Helper to decide if a query is related to file sharing
def is_file_sharing_query(query: str) -> bool:
    """Check if the query is related to file sharing."""
    keywords = ["find file", "search file", "look for file", "share file", 
                "find document", "search document", "download", "desktop file", 
                "find", "search"]
    return any(keyword in query.lower() for keyword in keywords)


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
4. **Sharing a file:**  
   ```json
   {
       "Message": "Okay I will look for the files , just a second",
       "Routing": {
           "Action": "Filesharing",
           "Details": "Here write the folder and all the details user has entered or even more"
       }
   }
   ```
"""

genai_old.configure(api_key=settings.GOOGLE_API_KEY)

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_schema": content.Schema(
    type = content.Type.OBJECT,
    enum = [],
    required = ["Message", "Routing"],
    properties = {
      "Message": content.Schema(
        type = content.Type.STRING,
      ),
      "Routing": content.Schema(
        type = content.Type.OBJECT,
        enum = [],
        required = ["Action", "Details"],
        properties = {
          "Action": content.Schema(
            type = content.Type.STRING,
          ),
          "Details": content.Schema(
            type = content.Type.STRING,
          ),
        },
      ),
    },
  ),
  "response_mime_type": "application/json",
}

model = genai_old.GenerativeModel(
  model_name="gemini-2.0-flash",
  generation_config=generation_config,
  system_instruction=system_prompt,
)


chat_session = model.start_chat()


@router.post("/router/")
async def route_query(query: UserQuery):
    """Routes the user's query to the appropriate action."""
    print(query.query)
    response = chat_session.send_message(query.query)
    return response.text

@router.post("/execute/")
async def execute_command(request: CommandRequest):
    """Executes a command if valid, otherwise stores it."""
    print(f"Executing command: {request.command}")
    
    if request.command == "Filesharing":
        initialize_file_server()
        # Process file sharing request
        query = request.details.get("query", "")
        
        # Use the file server to search for files
        if not file_server:
            return {"status": "error", "message": "File server not initialized"}
        
        # Interpret the query with Gemini if available
        search_params = file_server.interpret_query_with_gemini(query)
        search_directory = search_params.get("directory")
        search_query = search_params.get("query")
        
        # Find matching files
        matching_files = file_server.find_files(search_query, directory=search_directory)
        
        if matching_files:
            # Generate download links
            links = file_server.generate_download_links(matching_files)
            
            # Create a response with file information and links
            result = {
                "status": "success",
                "message": f"Found {len(links)} files matching '{search_query}'",
                "directory": search_directory,
                "search_query": search_query,
                "files": links
            }
        else:
            result = {
                "status": "not_found",
                "message": f"No files matching '{search_query}' were found",
                "directory": search_directory,
                "search_query": search_query,
                "files": []
            }
        
        return result
    else:
        # Your existing code for other commands
        if request.command != "NULL/Other":
            prompt = process_query(request.command)
            response = get_llm_response(
                prompt,
                """Your solo task is to choose a command...""",
            )
            if "python" in response:
                run_commands(response)
                return {"status": "success", "message": "Command executed"}
    
    return {"status": "success", "message": "Command processed"}

@router.post("/pinecone/search/")
async def pinecone_search(request: PineconeQuery):
    """Search in Pinecone index using the provided vector."""
    try:
        results = pinecone_index.query(
            vector=request.vector, top_k=request.top_k, include_metadata=True
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/pinecone/store/")
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

@router.post("/generate-code/")
async def generate_code(query: UserQuery):
    """Generate Python code for the given query using LLM."""
    try:
        response = get_llm_response(query.query)
        return {"code": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

