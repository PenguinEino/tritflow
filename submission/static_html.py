"""Freeze notebook controls at their real initial state in offline Chromium.

The saved PNG is a screenshot of the generated HTML, not a redrawn circuit or
estimated waveform. Plotly comes from the installed package; no CDN is needed.
"""

import asyncio
from pathlib import Path
import re


async def _snapshots(items, directory):
    from choreographer import Browser
    from plotly.offline import get_plotlyjs

    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    javascript = directory/"plotly.min.js"
    javascript.write_text(get_plotlyjs())
    results = []
    async with Browser(headless=True) as browser:
        for index, html in enumerate(items):
            # All plots must be rendered from the same installed Plotly as the
            # executing notebook. Other remote scripts are refused.
            html = re.sub(r'<script[^>]*src="https://cdn\.plot\.ly/[^"]+"[^>]*></script>',
                          '<script src="plotly.min.js"></script>', html)
            if re.search(r'<(?:script|img)[^>]*src=["\']https?://', html):
                raise ValueError("static HTML depends on an unbundled remote asset")
            page = directory/f"view-{index}.html"
            page.write_text('<!doctype html><html><head><meta charset="utf-8">'
                            '<style>body{margin:16px;background:white;color:#111;}'
                            'img{max-width:100%;}details{display:block;}</style></head><body>'
                            + html + '</body></html>')
            tab = await browser.create_tab()
            await tab.send_command("Page.enable")
            await tab.send_command("Emulation.setDeviceMetricsOverride", {
                "width": 1140, "height": 900, "deviceScaleFactor": 1, "mobile": False})
            await tab.send_command("Page.navigate", {"url": page.as_uri()})
            # Let Plotly's promise queue, fonts and raster images settle. The
            # readiness expression runs in the page and has a bounded timeout.
            ready = await tab.send_command("Runtime.evaluate", {
                "expression": """new Promise(async (resolve,reject)=>{
                    const end=Date.now()+30000;
                    while(document.readyState!=='complete'){
                        if(Date.now()>end){reject('page load timeout');return;}
                        await new Promise(r=>setTimeout(r,50));
                    }
                    await document.fonts.ready;
                    await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})));
                    await new Promise(r=>setTimeout(r,500));
                    const plots=[...document.querySelectorAll('.plotly-graph-div')];
                    if(plots.some(p=>!p._fullLayout)){reject('Plotly did not render');return;}
                    resolve({width:document.documentElement.scrollWidth,
                             height:document.documentElement.scrollHeight,
                             text:document.body.innerText});
                })""", "awaitPromise": True, "returnByValue": True})
            if ready.get("result", {}).get("exceptionDetails") or "error" in ready:
                raise ValueError(f"HTML snapshot failed: {ready}")
            dimensions = ready["result"]["result"]["value"]
            if dimensions["height"] > 12000 or dimensions["width"] > 3000:
                raise ValueError("HTML snapshot exceeds readable dimensions")
            screenshot = await tab.send_command("Page.captureScreenshot", {
                "format": "png", "captureBeyondViewport": True,
                "clip": {"x": 0, "y": 0, "width": dimensions["width"],
                         "height": dimensions["height"], "scale": 1}})
            results.append({"image/png": screenshot["result"]["data"],
                            "text/plain": dimensions["text"].strip()
                            + "\nSaved initial view; rerun for interactive controls."})
            await tab.close()
    return results


def snapshots(items, directory):
    """Render a batch with one browser; fail instead of publishing blank figures."""
    return asyncio.run(_snapshots(items, directory))
