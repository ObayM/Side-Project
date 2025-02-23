import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Launch the browser with options
        options = {
            'args': [
                '--disable-blink-features=AutomationControlled'
            ],
            'headless': False  # Set headless option here
        }
        browser = await p.chromium.launch(**options)
        context = browser.new_context(storage_state='gmail_storage_state.json')

    # Open a new page
        page = context.new_page()

        # 1. Go to https://mail.google.com
        await page.goto("https://mail.google.com")
        await asyncio.sleep(1)

        # 2. Locate the email field (usually labeled "Email or phone").
        await page.wait_for_selector("input[name='identifier']")
        email_field = page.locator("input[name='identifier']")

        # 3. Enter your email into the email field.
        await email_field.fill("zezoelkafoury005@gmail.com")
        await asyncio.sleep(1)

        # 4. Click the "Next" button.
        await page.locator("button:has-text('Next')").click()
        await asyncio.sleep(3)

        # 5. Locate the password field (usually labeled "Password").
        await page.wait_for_selector("input[name='Passwd']")
        password_field = page.locator("input[name='Passwd']")

        # 6. Enter your password into the password field.
        await password_field.fill("Myfamily1234%")
        await asyncio.sleep(1)

        # 7. Click the "Next" button.
        await page.locator("button:has-text('Next')").click()
        await asyncio.sleep(10)

        # 8. Save the storage state to a JSON file
        storage_file = "gmail_storage_state.json"
        await context.storage_state(path=storage_file)
        print(f"Storage state saved to {storage_file}")

        # Keep the browser open
        print("Done! Keeping browser open...")
        await asyncio.Future()

# Run the script
asyncio.run(main())