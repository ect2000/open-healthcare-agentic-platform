import asyncio
import os
import re

from playwright.async_api import async_playwright

SCREENSHOT_DIR = "docs/images"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


async def capture_k8s_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # 1. Streamlit Presets & UI on Kubernetes (port 8501)
        print("Capturing Kubernetes Streamlit UI...")
        await page.goto("http://localhost:8501", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # Trigger Preset 1
        preset_btn = page.get_by_role(
            "button", name=re.compile(r"1\.\s*Pediatric Dentist Discovery")
        )
        if await preset_btn.is_visible():
            await preset_btn.click()
            await page.wait_for_timeout(1000)

        search_btn = page.get_by_role("button", name=re.compile(r"Execute Healthcare Discovery"))
        if await search_btn.is_visible():
            await search_btn.click()
            print("Executing Healthcare Discovery on Kubernetes Streamlit UI...")
            # Wait for search and inference execution
            await page.wait_for_timeout(25000)

        await page.screenshot(path=f"{SCREENSHOT_DIR}/m09_kubernetes_streamlit.png", full_page=True)
        print("Saved docs/images/m09_kubernetes_streamlit.png")

        # 2. Grafana Dashboard on Kubernetes (port 3000)
        print("Capturing Kubernetes Grafana Dashboard...")
        await page.goto(
            "http://localhost:3000/d/healthcare-observability/open-healthcare-agentic-ai-observability?orgId=1&refresh=5s",
            wait_until="networkidle",
        )
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/m09_kubernetes_grafana.png")
        print("Saved docs/images/m09_kubernetes_grafana.png")

        # 3. Grafana Tempo Traces (Explore on port 3000)
        print("Capturing Kubernetes Tempo Trace Explorer...")
        trace_id = "a347be871b05b2c44c5a757b1c6da0d3"
        await page.goto(
            f"http://localhost:3000/explore?orgId=1&left=%7B%22datasource%22:%22tempo%22,%22queries%22:%5B%7B%22queryType%22:%22traceId%22,%22query%22:%22{trace_id}%22%7D%5D,%22range%22:%7B%22from%22:%22now-1h%22,%22to%22:%22now%22%7D%7D",
            wait_until="networkidle",
        )
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/m09_kubernetes_tempo.png")
        print("Saved docs/images/m09_kubernetes_tempo.png")

        # 4. Kubernetes Workloads Terminal View
        print("Capturing Kubernetes Workloads screenshot...")
        # Create a clean HTML page displaying real kubectl get pods, svc, and nodes output
        import subprocess

        kubectl_pods = subprocess.run(
            ["kubectl", "get", "pods", "-n", "open-healthcare", "-o", "wide"],
            capture_output=True,
            text=True,
        ).stdout
        kubectl_svc = subprocess.run(
            ["kubectl", "get", "svc", "-n", "open-healthcare"], capture_output=True, text=True
        ).stdout
        kubectl_nodes = subprocess.run(
            ["kubectl", "get", "nodes", "-o", "wide"], capture_output=True, text=True
        ).stdout

        html_workloads = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 30px;
    background-color: #0b0f19;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #f8fafc;
    width: 1300px;
  }}
  h1 {{
    font-size: 20px;
    color: #38bdf8;
    margin-bottom: 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  .section {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 20px;
  }}
  .sec-title {{
    color: #34d399;
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 10px;
  }}
  pre {{
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
    color: #e2e8f0;
    overflow-x: auto;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    background: #0284c7;
    color: #fff;
    margin-left: 10px;
  }}
</style>
</head>
<body>
  <h1>Kubernetes Cluster Workloads & Status <span class="badge">Namespace: open-healthcare</span></h1>
  
  <div class="section">
    <div class="sec-title">$ kubectl get nodes -o wide</div>
    <pre>{kubectl_nodes}</pre>
  </div>

  <div class="section">
    <div class="sec-title">$ kubectl get pods -n open-healthcare -o wide</div>
    <pre>{kubectl_pods}</pre>
  </div>

  <div class="section">
    <div class="sec-title">$ kubectl get svc -n open-healthcare</div>
    <pre>{kubectl_svc}</pre>
  </div>
</body>
</html>"""
        with open("temp_k8s_workloads.html", "w") as f:
            f.write(html_workloads)

        await page.goto(f"file://{os.path.abspath('temp_k8s_workloads.html')}")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/m09_kubernetes_workloads.png", full_page=True)
        print("Saved docs/images/m09_kubernetes_workloads.png")

        if os.path.exists("temp_k8s_workloads.html"):
            os.remove("temp_k8s_workloads.html")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(capture_k8s_screenshots())
