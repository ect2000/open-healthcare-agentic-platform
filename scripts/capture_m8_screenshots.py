import asyncio

from playwright.async_api import async_playwright


async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Streamlit UI with Execution Trace
        print("Capturing Streamlit...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        # Click on preset 2
        preset_btn = page.get_by_role("button", name="2. Best Pediatric Dentists + Research")
        if await preset_btn.is_visible():
            await preset_btn.click()
            await page.wait_for_timeout(1000)

        search_btn = page.get_by_role("button", name="Execute Healthcare Discovery")
        if await search_btn.is_visible():
            await search_btn.click()
            # Wait for completion
            await page.wait_for_timeout(25000)

        import re

        obs_tab = page.get_by_role("tab", name=re.compile(r"Telemetry"))
        if await obs_tab.is_visible():
            await obs_tab.click()
            await page.wait_for_timeout(1500)

        await page.screenshot(path="docs/images/m08_streamlit_trace.png", full_page=True)
        print("Saved docs/images/m08_streamlit_trace.png")

        # 2. Grafana Dashboard - Platform Overview
        print("Capturing Grafana Platform Overview...")
        await page.goto(
            "http://localhost:3000/d/healthcare-observability/open-healthcare-agentic-ai-observability?orgId=1&refresh=5s",
            wait_until="networkidle",
        )
        await page.wait_for_timeout(4000)
        await page.screenshot(path="docs/images/m08_platform_overview.png")
        print("Saved docs/images/m08_platform_overview.png")

        # Scroll to agent workflow & retrieval metrics
        await page.evaluate("window.scrollBy(0, 450)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/images/m08_agent_workflow.png")
        print("Saved docs/images/m08_agent_workflow.png")

        await page.evaluate("window.scrollBy(0, 450)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/images/m08_retrieval_metrics.png")
        print("Saved docs/images/m08_retrieval_metrics.png")

        await page.evaluate("window.scrollBy(0, 450)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/images/m08_evidence_quality.png")
        print("Saved docs/images/m08_evidence_quality.png")

        await page.evaluate("window.scrollBy(0, 450)")
        await page.wait_for_timeout(1000)
        await page.screenshot(path="docs/images/m08_gemma4_inference.png")
        print("Saved docs/images/m08_gemma4_inference.png")

        # 3. Grafana Tempo Trace Explore
        print("Capturing Grafana Tempo Trace...")
        await page.goto(
            "http://localhost:3000/explore?schemaVersion=1&panes=%7B%22a%22%3A%7B%22datasource%22%3A%22tempo%22%7D%7D"
        )
        await page.wait_for_timeout(2000)

        search_btn = page.get_by_role("radio", name="Search")
        if await search_btn.count() > 0:
            await search_btn.first.click()
            await page.wait_for_timeout(1000)

        run_btn = page.get_by_role("button", name="Run query")
        if await run_btn.count() > 0:
            await run_btn.first.click()
            await page.wait_for_timeout(3000)

        await page.screenshot(path="docs/images/m08_tempo_trace.png")
        print("Saved docs/images/m08_tempo_trace.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_screenshots())
