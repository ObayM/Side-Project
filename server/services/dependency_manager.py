from openai import OpenAI
import os
import platform
import ast
import re
from dotenv import load_dotenv

load_dotenv()

def has_imports(code: str) -> bool:
    """
    Check if the Python code contains any import statements.
    Returns True if imports are found, False otherwise.
    """
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return True
        return False
    except SyntaxError:
        print("The code has errors")
        return False

def create_virtual_env():
    if platform.system() != "Windows":
        os.system("python -m venv venv")
        os.system("source venv/bin/activate")

def install_packages(requirements: str) -> bool:
    """
    Install packages from requirements string.
    Returns True if installation was successful, False otherwise.
    """
    try:
        requirements = requirements.strip()
        if not requirements:
            print("No valid requirements found")
            return False

        with open("/temp/requirements.txt", 'w') as f:
            f.write(requirements)

        result = os.system(f"pip install -r temp/requirements.txt")
        return result == 0

    except Exception as e:
        print(f"Error installing packages: {e}")
        return False

def get_requirements(code: str, client: OpenAI) -> str:
    """Get requirements.txt content from the API."""
    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-3.1-70b-instruct:free",
            messages=[
                {
                    "role": "system",
                    "content": "You are a software engineer. Your only task is to create the requirements.txt file based on the provided Python code. Return only the requirements.txt content with no additional explanation."
                },
                {
                    "role": "user",
                    "content": code
                }
            ]
        )
        
        response = completion.choices[0].message.content
        
        # Clean the response
        requirements = re.sub(r'```.*?\n|```|requirements\.txt', '', response, flags=re.DOTALL)
        return requirements.strip()
        
    except Exception as e:
        print(f"Error getting requirements: {e}")
        return ""

def main(code: str):
    if not code or not code.strip():
        print("Error: No code provided")
        return

    # Check if code has any imports first
    if not has_imports(code):
        print("No imports found in the code. Skipping package installation.")
        return

    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv('API_KEY_OPENROUTER'),
        )

        requirements = get_requirements(code, client)
        if not requirements:
            print("Failed to generate requirements")
            return

        if platform.system() != "Windows":
            create_virtual_env()

        if install_packages(requirements):
            print("Successfully installed all packages")
        else:
            print("Failed to install some packages")

    except Exception as e:
        print(f"An error occurred: {e}")