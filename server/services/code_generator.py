import google.generativeai as genai
import os
import install_dencencies
from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

def read_prompt():
    try:
        with open('prompt.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Error: prompt.txt file not found!")
        return None
    except Exception as e:
        print(f"Error reading prompt.txt: {str(e)}")
        return None

def get_code_from_gemini(prompt):
    """Get code generation from Gemini"""
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-exp-1206')
        
        # Add specific instruction to generate only code
        enhanced_prompt = f"""
        Generate only Python code without any explanations or markdown formatting.
        The code should address the following request:
        {prompt}
        Provide only the executable Python code without any additional text.
        """
        
        # Generate response
        response = model.generate_content(enhanced_prompt)
        
        # Extract code from response
        generated_code = response.text.strip()
        
        # Remove markdown code blocks if present
        if generated_code.startswith("```python"):
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()
        
        return generated_code
    
    except Exception as e:
        print(f"Error generating code with Gemini: {str(e)}")
        return None

def execute_code(code):
    """Execute the generated code"""
    try:
        print("\nExecuting generated code:")
        print("-" * 50)
        print(code)
        print("-" * 50)
        print("\nOutput:")
        with open('generated_code.py','w+') as f:
            f.writelines(code)

        os.system('python3 generated_code.py')
    except Exception as e:
        print(f"Error executing code: {str(e)}")

def main():
    prompt = read_prompt()
    if not prompt:
        return
    
    generated_code = get_code_from_gemini(prompt)
    if not generated_code:
        return
    
    install_dencencies.main(generated_code)
    
    execute_code(generated_code)

if __name__ == "__main__":
    main()