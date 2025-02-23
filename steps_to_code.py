import google.generativeai as genai
import os
import re
import asyncio
from playwright.async_api import async_playwright

GOOGLE_API_KEY = "AIzaSyBxE9MQdeQuH2uIOHO23QslC6uYnSSka-g"
genai.configure(api_key=GOOGLE_API_KEY)

system_prompt = """
# **AI Interpreter: Playwright Python Code Generator**
You convert step-by-step instructions into valid Playwright Python scripts. The input will include the **page source code** (HTML) of the current webpage. Your task is to analyze the HTML and generate the best selectors for the requested elements.

### **Your Tasks:**
1. **Analyze the Page Source Code:**
   - Use the provided HTML to identify the best selectors for the requested elements.
   - Prefer **stable and unique selectors** (e.g., `data-testid`, `aria-label`, or `role` attributes).
   - Avoid using fragile selectors like hardcoded class names or IDs.

2. **Generate Playwright Code:**
   - Use the identified selectors to generate Playwright Python code.
   - Ensure the code is asynchronous (`async def`) and includes proper error handling.

3. **Dynamic Element Handling:**
   - Use `await page.wait_for_selector(selector)` to ensure elements are loaded before interaction.

4. **Stability:**
   - Insert `await asyncio.sleep(1)` between actions for stability.

5. **Browser Launch:**
   - Launch the browser in non-headless mode (`headless=False`) for debugging.
   - Use Chromium as the default browser.

6. **Code Formatting:**
   - Output must be valid Python code.
   - Remove any non-UTF-8 characters or markdown formatting.

7. **Make sure the code is complete and can be executed without any errors** 

8. ** If the task is related to gmail or email:
   - use the json context file
    - context = await browser.new_context(storage_state='gmail_storage_state.json')
    - page = await context.new_page()
    - know that the compose button is already clicked and the input is focused on the "TO" input
    - ADD time.sleep(9) before excecuting the code to wait for the page to load

9. ** If you cant locate the correct button or div for an action then click on the text item:
    **Example**
    -you did not find the compose button when you want to send email then click on the word compose
    ** Do this for all websites that doesnt work

10. ** Remember that when you click on the compose button on gmail it automaticly focuses on the to input so start typing the recipient email address instantly**

11. **Use only selectors based on the HTML structure provided to you in the input, dont use elements outside the input**

12. ** Make to sure to avoid this error async with sync_playwright() as playwright:
AttributeError: __aenter__**

13. ** Include long timeout to wait for each element to load**
    - Do not include timeout in the type function

14. ** Do not use **async with sync_playwright()** **!Important**

15. Make sure to avoid this error: raise Error(
playwright._impl._errors.Error: **It looks like you are using Playwright Sync API inside the asyncio loop.
Please use the Async API instead.** **!Important**

16. Make sure the code is complete and can be executed without any syntax errors or any other errors.

17. **Generate Asynchronous Code**:
   - Use `async_playwright` and `async`/`await` for all Playwright interactions.
   - Ensure the code is compatible with `asyncio`.
"""

async def get_page_content(page):
    """Extract the HTML content of the current page."""
    return await page.content()

def extract_url_from_steps(steps):
    """Extract the target URL from the user's instructions."""
    url_pattern = r"https?://[^\s]+"
    match = re.search(url_pattern, steps)
    if match:
        return match.group(0)
    else:
        return "https://www.youtube.com"  # Default URL

def read_steps():
    try:
        with open('steps.txt', 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print("Error: steps.txt file not found!")
        return None
    except Exception as e:
        print(f"Error reading steps.txt: {str(e)}")
        return None

def get_code_from_gemini(prompt, page_content):
    """Get code generation from Gemini."""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            system_instruction=system_prompt
        )

        full_prompt = f"{prompt}\n\n**Page Source Code (HTML):**\n```html\n{page_content}\n```"
        print(full_prompt)
        response = model.generate_content(full_prompt)
        generated_code = response.text.strip()

        if generated_code.startswith("```python"):
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()

        return generated_code
    except Exception as e:
        print(f"Error generating code with Gemini: {str(e)}")
        return None

def execute_code(code):
    """Execute the generated code."""
    try:
        print("\nExecuting generated code:")
        print("-" * 50)
        print(code)
        print("-" * 50)
        print("\nOutput:")
        with open('generated_steps_code.py', 'w+') as f:
            f.writelines(code)

        os.system('python generated_steps_code.py')
    except Exception as e:
        print(f"Error executing code: {str(e)}")

async def extract_page_structure(page):
    """Extract the page structure (text, buttons, inputs, divs)."""
    return await page.evaluate('''() => {
        // Extract text content from the entire body
        const allText = document.body.innerText;

        // Extract buttons
        const buttons = Array.from(document.querySelectorAll('button')).map(button => ({
            text: button.innerText,
            type: button.type,
            disabled: button.disabled
        }));

        // Extract inputs
        const inputs = Array.from(document.querySelectorAll('input')).map(input => ({
            type: input.type,
            placeholder: input.placeholder,
            value: input.value,
            id: input.id,
            name: input.name
        }));

        // Extract divs
        const divs = Array.from(document.querySelectorAll('div')).map(div => ({
            id: div.id,
            className: div.className,
            text: div.innerText
        }));

        // Return the extracted data
        return {
            allText,
            buttons,
            inputs,
            divs
        };
    }''')

async def main():
    steps = read_steps()
    if not steps:
        return

    async with async_playwright() as p:
        options = {
            'args': [
                '--disable-blink-features=AutomationControlled'
            ],
            'headless': True  # Set headless option here
        }
        browser = await p.chromium.launch(**options)
        context = await browser.new_context(storage_state='gmail_storage_state.json')
        page = await context.new_page()
        await page.route('**/*.{png,jpg,jpeg,svg,gif,webp,mp4,mp3,js,css}', lambda route: route.abort())

        # Extract the target URL from the steps
        target_url = extract_url_from_steps(steps)
        print(f"Navigating to: {target_url}")

        # Navigate to the target website
        await page.goto(target_url)
        await asyncio.sleep(1)  # Wait for the page to load

        # Extract the page structure
        result = await extract_page_structure(page)
        # print("All Text:", result['allText'])
        # print("Buttons:", result['buttons'])
        # print("Inputs:", result['inputs'])
        # print("Divs:", result['divs'])

        # Generate Playwright code using the LLM
        generated_code = get_code_from_gemini(steps, result)
        if not generated_code:
            return

        # Execute the generated code
        execute_code(generated_code)

        # Check for redirections and update the page content
        current_url = page.url
        await asyncio.sleep(2)  # Wait for potential redirection
        if current_url != page.url:  # Check if the URL has changed
            print(f"Page redirected to: {page.url}")

            # Extract the updated page structure
            result = await extract_page_structure(page)
            print("All Text (Updated):", result['allText'])
            print("Buttons (Updated):", result['buttons'])
            print("Inputs (Updated):", result['inputs'])
            print("Divs (Updated):", result['divs'])

            # Regenerate and execute the updated code
            generated_code = get_code_from_gemini(steps, result)
            if generated_code:
                execute_code(generated_code)

        # Close the browser
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())