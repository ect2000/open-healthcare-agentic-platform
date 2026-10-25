import os

from playwright.sync_api import sync_playwright

html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 30px;
    background-color: #0b0f19;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #f8fafc;
    width: 1200px;
    box-sizing: border-box;
  }
  .title-bar {
    text-align: center;
    margin-bottom: 25px;
  }
  h1 {
    margin: 0 0 8px 0;
    font-size: 26px;
    letter-spacing: -0.5px;
    color: #f8fafc;
  }
  .subtitle {
    color: #94a3b8;
    font-size: 14px;
  }
  .host-box {
    border: 2px dashed #0284c7;
    border-radius: 14px;
    padding: 24px;
    background: rgba(14, 165, 233, 0.03);
    position: relative;
    margin-bottom: 25px;
  }
  .host-badge {
    position: absolute;
    top: -12px;
    left: 24px;
    background: #0284c7;
    color: #ffffff;
    padding: 2px 14px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .k8s-cluster {
    border: 2px solid #10b981;
    border-radius: 12px;
    padding: 24px;
    background: #0f172a;
    position: relative;
    margin-bottom: 24px;
  }
  .k8s-badge {
    position: absolute;
    top: -12px;
    left: 24px;
    background: #10b981;
    color: #ffffff;
    padding: 2px 14px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 10px;
  }
  .card {
    background: #1e293b;
    border-radius: 10px;
    padding: 16px;
    border: 1px solid #334155;
    position: relative;
  }
  .card-api { border-top: 4px solid #6366f1; }
  .card-ui { border-top: 4px solid #ec4899; }
  .card-otel { border-top: 4px solid #eab308; }
  .card-prom { border-top: 4px solid #ef4444; }
  .card-tempo { border-top: 4px solid #06b6d4; }
  .card-grafana { border-top: 4px solid #f97316; }
  
  .card-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .badge {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    background: #334155;
    color: #94a3b8;
  }
  .card-desc {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 12px;
  }
  .endpoint {
    background: #0f172a;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 11px;
    color: #38bdf8;
    margin-top: 4px;
  }
  .host-runtime {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #1c1917;
    border: 1.5px solid #d97706;
    border-radius: 10px;
    padding: 18px 24px;
  }
  .runtime-info h3 {
    margin: 0 0 4px 0;
    font-size: 16px;
    color: #fbbf24;
  }
  .runtime-info p {
    margin: 0;
    font-size: 12px;
    color: #d6d3d1;
  }
  .routes {
    display: flex;
    gap: 12px;
    margin-top: 18px;
    font-size: 11px;
    color: #cbd5e1;
    background: #090d16;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #1e293b;
  }
  .route-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
</style>
</head>
<body>

<div class="title-bar">
  <h1>Kubernetes-Native Architecture (Kind Local Cluster)</h1>
  <div class="subtitle">Open Healthcare Agentic Platform &bull; Milestone M9 Deployment Architecture</div>
</div>

<div class="host-box">
  <div class="host-badge">macOS Host Machine &bull; Gateway: 172.18.0.1 (host.docker.internal)</div>
  
  <div class="k8s-cluster">
    <div class="k8s-badge">Kind Kubernetes Cluster &bull; Namespace: open-healthcare</div>
    
    <div class="grid">
      <!-- API -->
      <div class="card card-api">
        <div class="card-title">
          <span>open-healthcare-api</span>
          <span class="badge">Backend</span>
        </div>
        <div class="card-desc">FastAPI Gateway & LangGraph Multi-Agent Engine</div>
        <div class="endpoint">ClusterIP: open-healthcare-api:8000</div>
        <div class="endpoint">NodePort: 30080 &rarr; Host 8000</div>
      </div>

      <!-- UI -->
      <div class="card card-ui">
        <div class="card-title">
          <span>open-healthcare-ui</span>
          <span class="badge">Frontend</span>
        </div>
        <div class="card-desc">Streamlit UI & Observability Hub (6 Presets)</div>
        <div class="endpoint">ClusterIP: open-healthcare-ui:8501</div>
        <div class="endpoint">NodePort: 30851 &rarr; Host 8501</div>
      </div>

      <!-- OTel Collector -->
      <div class="card card-otel">
        <div class="card-title">
          <span>otel-collector</span>
          <span class="badge">Telemetry</span>
        </div>
        <div class="card-desc">OpenTelemetry Ingestion & Pipeline Router</div>
        <div class="endpoint">OTLP gRPC: 4317 &bull; HTTP: 4318</div>
        <div class="endpoint">Metrics Scrape Exporter: 8889</div>
      </div>

      <!-- Prometheus -->
      <div class="card card-prom">
        <div class="card-title">
          <span>prometheus</span>
          <span class="badge">Metrics</span>
        </div>
        <div class="card-desc">Time-Series Metrics Collection Engine</div>
        <div class="endpoint">ClusterIP: prometheus:9090</div>
        <div class="endpoint">NodePort: 30090 &rarr; Host 9090</div>
      </div>

      <!-- Tempo -->
      <div class="card card-tempo">
        <div class="card-title">
          <span>tempo</span>
          <span class="badge">Tracing</span>
        </div>
        <div class="card-desc">Distributed Trace Storage & Search Backend</div>
        <div class="endpoint">ClusterIP: tempo:3200</div>
        <div class="endpoint">NodePort: 30200 &rarr; Host 3200</div>
      </div>

      <!-- Grafana -->
      <div class="card card-grafana">
        <div class="card-title">
          <span>grafana</span>
          <span class="badge">Dashboards</span>
        </div>
        <div class="card-desc">Pre-provisioned Healthcare Observability Dashboards</div>
        <div class="endpoint">ClusterIP: grafana:3000</div>
        <div class="endpoint">NodePort: 30300 &rarr; Host 3000</div>
      </div>
    </div>

    <div class="routes">
      <div class="route-item"><div class="dot" style="background:#ec4899"></div> UI &rarr; API Service Discovery: <code>http://open-healthcare-api:8000</code></div>
      <div class="route-item"><div class="dot" style="background:#eab308"></div> App Telemetry &rarr; OTel: <code>http://otel-collector:4318</code></div>
      <div class="route-item"><div class="dot" style="background:#f97316"></div> Grafana Datasources: <code>prometheus:9090</code>, <code>tempo:3200</code></div>
    </div>
  </div>

  <div class="host-runtime">
    <div class="runtime-info">
      <h3>Native macOS Ollama Runtime (Apple Silicon Metal GPU)</h3>
      <p>Preserved native host execution for sub-second Gemma 4 inference &bull; Reachable from Kind Pods via <code>host.docker.internal:11434</code> (Gateway <code>172.18.0.1</code>)</p>
    </div>
    <div class="endpoint" style="font-size:12px; border:1px solid #78350f; color:#fde68a;">
      Model: gemma4:e2b &bull; Port: 11434
    </div>
  </div>
</div>

</body>
</html>
"""

with open("temp_k8s_arch.html", "w") as f:
    f.write(html_content)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1260, "height": 720})
    page.goto(f"file://{os.path.abspath('temp_k8s_arch.html')}")
    page.wait_for_timeout(500)
    page.screenshot(path="docs/images/m09_kubernetes_architecture.png", full_page=True)
    browser.close()

if os.path.exists("temp_k8s_arch.html"):
    os.remove("temp_k8s_arch.html")

print("Created docs/images/m09_kubernetes_architecture.png successfully")
