#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/public"
SITE="https://trendscout.pages.dev"

rm -rf "$OUT"
mkdir -p "$OUT/dashboard" "$OUT/reports" "$OUT/about"

cp "$ROOT/dashboard/index.html" "$OUT/dashboard/index.html"
cp "$ROOT/reports/latest.json" "$OUT/reports/latest.json"
cp "$ROOT/reports/latest.md" "$OUT/reports/latest.md"

cat > "$OUT/index.html" <<'HTML'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#0b1020">
<meta name="description" content="Find rising GitHub projects across AI agents, MCP servers, local LLMs, coding assistants and developer tools. Explore transparent trend signals and measured star growth with TrendScout.">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="https://trendscout.pages.dev/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="TrendScout">
<meta property="og:title" content="TrendScout — Find What's Rising on GitHub">
<meta property="og:description" content="Discover emerging AI agents, MCP servers, local AI and developer tools using public GitHub data.">
<meta property="og:url" content="https://trendscout.pages.dev/">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="TrendScout — GitHub Trend Radar">
<meta name="twitter:description" content="Find rising open-source projects across AI and developer tooling.">
<title>TrendScout — Find Rising GitHub Projects & AI Developer Tools</title>
<script type="application/ld+json">
{
  "@context":"https://schema.org",
  "@type":"WebSite",
  "name":"TrendScout",
  "url":"https://trendscout.pages.dev/",
  "description":"An open-source radar for discovering rising GitHub repositories across AI agents, MCP, local AI and developer tools."
}
</script>
<style>
:root{color-scheme:dark;--bg:#0b1020;--panel:#121a2d;--line:#26334d;--text:#e8eefc;--muted:#aab7ce;--accent:#9bb0ff;--green:#63d6a5}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#182746 0,#0b1020 58%);color:var(--text);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:960px;margin:auto;padding:34px 20px 70px}.brand{font-size:12px;letter-spacing:.16em;color:var(--accent);font-weight:800}
.hero{padding:54px 0 28px}.hero h1{font-size:clamp(40px,8vw,68px);line-height:1.02;letter-spacing:-.045em;margin:12px 0 18px}.hero p{max-width:740px;color:var(--muted);font-size:18px}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:26px 0}.btn{display:inline-block;padding:12px 18px;border-radius:10px;text-decoration:none;font-weight:700;border:1px solid var(--line);color:var(--text);background:var(--panel)}.btn.primary{background:#dce5ff;color:#111a30;border-color:#dce5ff}
section{margin:36px 0}.panel{background:linear-gradient(145deg,#141f35,#10182a);border:1px solid var(--line);border-radius:16px;padding:22px}.cols{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}h2{font-size:24px;letter-spacing:-.02em}h3{margin:0 0 8px}p,li{color:var(--muted)}a{color:var(--accent)}.small{font-size:13px;color:var(--muted)}footer{border-top:1px solid var(--line);padding-top:20px;color:var(--muted);font-size:13px}
@media(max-width:650px){main{padding:24px 15px 50px}.hero{padding-top:38px}.cols{grid-template-columns:1fr}.hero p{font-size:16px}}
</style>
</head>
<body><main>
<div class="brand">TREND RADAR / OPEN SOURCE</div>
<header class="hero">
<h1>Find what's rising on GitHub.</h1>
<p>TrendScout helps developers discover promising open-source projects before they get lost in the noise. Explore emerging AI agents, Model Context Protocol (MCP) servers, local LLM tools, coding assistants and developer automation.</p>
<div class="actions"><a class="btn primary" href="/dashboard/">Explore the live trend dashboard →</a><a class="btn" href="https://github.com/Coolrj-1/TrendScout">View the open-source project</a></div>
</header>
<section class="cols">
<article class="panel"><h2>Discover emerging tools</h2><p>Browse repositories grouped by developer-focused categories. Search by project name, topic or description, filter categories and sort by stars, recent activity or available growth data.</p></article>
<article class="panel"><h2>Separate popularity from momentum</h2><p>Total stars show accumulated interest. Seven-day star change is shown only when comparable historical snapshots exist, so missing history is not presented as measured growth.</p></article>
</section>
<section>
<h2>What can you explore?</h2>
<div class="cols">
<article class="panel"><h3>AI agents & coding assistants</h3><p>Open-source agents, agentic workflows, coding copilots and tools that help automate software development.</p></article>
<article class="panel"><h3>MCP servers & integrations</h3><p>Model Context Protocol servers and integrations that connect AI applications to tools, data and services.</p></article>
<article class="panel"><h3>Local AI & LLM inference</h3><p>Projects for running models locally, private inference, self-hosted AI and efficient developer workflows.</p></article>
<article class="panel"><h3>Automation & creator tools</h3><p>Browser and desktop automation, AI video workflows and practical tools for builders and creators.</p></article>
</div>
</section>
<section class="panel">
<h2>How TrendScout works</h2>
<ol>
<li>Searches public GitHub repository metadata using configurable topic queries.</li>
<li>Records repository stars, forks, language, topics and update activity in dated snapshots.</li>
<li>Compares current stars with an earlier snapshot when a comparable history exists.</li>
<li>Publishes a ranked report and an interactive dashboard.</li>
</ol>
<p class="small">Trend scores are heuristic discovery signals, not endorsements or measures of software quality. TrendScout does not clone repositories or execute their code.</p>
<p><a href="/about/">Read the methodology</a> · <a href="/reports/latest.md">Read the latest report</a></p>
</section>
<section><h2>Built in the open</h2><p>TrendScout is an open-source project. Explore the source, inspect the scanner and suggest improvements on GitHub.</p><p><a href="https://github.com/Coolrj-1/TrendScout">GitHub repository →</a></p></section>
<footer>TrendScout · Independent open-source discovery · <a href="/dashboard/">Dashboard</a> · <a href="/about/">Methodology</a></footer>
</main></body></html>
HTML

cat > "$OUT/about/index.html" <<'HTML'
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Learn how TrendScout searches public GitHub repositories, stores daily snapshots and estimates star growth.">
<meta name="robots" content="index,follow"><link rel="canonical" href="https://trendscout.pages.dev/about/">
<title>TrendScout Methodology — How GitHub Trends Are Measured</title></head>
<body style="max-width:800px;margin:40px auto;padding:0 18px;font:16px/1.7 system-ui;background:#0b1020;color:#e8eefc">
<p><a href="/">← TrendScout home</a></p><h1>TrendScout methodology</h1>
<p>TrendScout is an open-source discovery tool that searches public GitHub repository metadata across configurable developer topics.</p>
<h2>Data collected</h2><p>The scanner records public repository fields such as name, description, URL, stars, forks, language, topics, creation time and last-push time. Dated snapshots are stored in the repository.</p>
<h2>Growth estimates</h2><p>When a comparable snapshot from roughly 6–8 days earlier exists, TrendScout calculates seven-day star change as current stars minus previous stars. Growth rate is calculated relative to the previous star count. If there is no comparable snapshot, growth is left unmeasured rather than guessed.</p>
<h2>Trend score</h2><p>The ranking heuristic combines absolute star growth, relative growth and repository freshness. It is a discovery aid, not a quality score, endorsement or investment signal. Search coverage and API limits can affect results.</p>
<h2>Privacy and safety</h2><p>TrendScout reads public GitHub metadata. It does not clone repositories, execute their code or collect private user data.</p>
<p><a href="/dashboard/">Explore the dashboard →</a> · <a href="https://github.com/Coolrj-1/TrendScout">Inspect the source on GitHub</a></p>
</body></html>
HTML

cat > "$OUT/robots.txt" <<'ROBOTS'
User-agent: *
Allow: /
Sitemap: https://trendscout.pages.dev/sitemap.xml
ROBOTS

cat > "$OUT/sitemap.xml" <<'SITEMAP'
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://trendscout.pages.dev/</loc></url>
  <url><loc>https://trendscout.pages.dev/dashboard/</loc></url>
  <url><loc>https://trendscout.pages.dev/about/</loc></url>
  <url><loc>https://trendscout.pages.dev/reports/latest.md</loc></url>
</urlset>
SITEMAP

cat > "$OUT/_headers" <<'HEADERS'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
HEADERS

echo "Cloudflare Pages output prepared at: $OUT"
