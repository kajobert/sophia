from playwright.sync_api import sync_playwright, expect

def verify_chat_static():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Jdi na lokální HTML soubor
        page.goto("file:///app/frontend/chat.html")

        # Chvíli počkej, aby se stránka vykreslila
        page.wait_for_timeout(1000)

        # Zadej zprávu
        page.fill("#message-input", "This is a static test.")

        # Klikni na tlačítko odeslat
        page.click("button:has-text('Send')")

        # Ověř, že se zpráva uživatele zobrazila
        expect(page.locator(".user-message")).to_have_text("This is a static test.")

        # Udělej screenshot, i když připojení selhalo
        page.screenshot(path="jules-scratch/verification/verification.png")

        print("Static verification screenshot captured.")

        browser.close()

if __name__ == "__main__":
    verify_chat_static()
