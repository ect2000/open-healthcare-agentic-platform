import asyncio
import os

from playwright.async_api import async_playwright


async def main():
    os.makedirs("docs/images", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1100})
        page = await context.new_page()

        print("Navigating to Streamlit UI at http://localhost:8501...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 1. Capture initial page
        await page.screenshot(path="docs/images/m07_ui_initial.png", full_page=True)
        print("Captured initial page screenshot")

        # 2. Trigger search
        search_btn = page.locator('button:has-text("Search")').first
        await search_btn.click()
        print("Clicked search button; waiting for results...")

        # Wait for the results to load
        await page.wait_for_selector("text=Grounded Synthesis (Gemma 4)", timeout=60000)
        await page.wait_for_timeout(3000)

        # Capture search results overview
        await page.screenshot(path="docs/images/m07_search_results.png", full_page=False)
        print("Captured search results overview")

        # 3. Click on "Agent Workflow & Query Fan-Out" tab
        workflow_tab = page.locator('[role="tab"]:has-text("Agent Workflow & Query Fan-Out")')
        await workflow_tab.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="docs/images/m07_workflow_fanout.png", full_page=False)
        print("Captured workflow and fan-out tab")

        # 4. Click on "Execution Telemetry" tab
        telemetry_tab = page.locator('[role="tab"]:has-text("Execution Telemetry")')
        await telemetry_tab.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="docs/images/m07_execution_telemetry.png", full_page=False)
        print("Captured execution telemetry tab")

        # 5. Click on "Patient Education" tab
        edu_tab = page.locator('[role="tab"]:has-text("Patient Education")')
        await edu_tab.click()
        await page.wait_for_timeout(2000)
        await page.screenshot(path="docs/images/m07_patient_education.png", full_page=False)
        print("Captured patient education tab")

        await browser.close()
        print("Playwright capture complete!")


if __name__ == "__main__":
    asyncio.run(main())
