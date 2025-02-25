import os
import socket
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import difflib
import argparse
from google import genai
import re

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
            links.append((file_path, link))
            
        return links

def main():
    parser = argparse.ArgumentParser(description="Smart File Server with Gemini-powered Search")
    parser.add_argument("-d", "--directory", help="Directory to serve files from", default=None)
    parser.add_argument("-p", "--port", help="Port to run the server on", type=int, default=8000)
    parser.add_argument("-q", "--query", help="Natural language query to find files", required=True)
    parser.add_argument("-k", "--api-key", help="Gemini API key", default=None)
    args = parser.parse_args()
    
    # Initialize and start the server
    server = FileServer(directory=args.directory, port=args.port, api_key=args.api_key)
    
    try:
        if server.start_server():
            # Process the natural language query with Gemini if enabled
            search_params = server.interpret_query_with_gemini(args.query)
            
            # Check if we should search in a different directory
            search_directory = search_params.get('directory')
            search_query = search_params.get('query')
            
            print(f"\nInterpreted query: '{search_query}'")
            if search_directory != server.directory:
                print(f"Searching in directory: {search_directory}")
            
            # Search for files matching the query
            matching_files = server.find_files(search_query, directory=search_directory)
            
            if matching_files:
                # Generate and display download links
                links = server.generate_download_links(matching_files)
                
                print("\n🔍 Top matching files found:")
                print("-" * 60)
                
                for i, (file, link) in enumerate(links, 1):
                    print(f"{i}. {os.path.basename(file)}")
                    print(f"   📁 {file}")
                    print(f"   ➤ {link}")
                    print()
                
                print("-" * 60)
                print("📋 Copy-paste friendly links:")
                for _, link in links:
                    print(link)
            else:
                print(f"No files matching '{search_query}' were found.")
                
            print("\nServer is running. Press Ctrl+C to stop.")
            
            # Keep the server running until manually stopped
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down server...")
                server.stop_server()
                
    except Exception as e:
        print(f"Error: {e}")
        if server:
            server.stop_server()

if __name__ == "__main__":
    main()