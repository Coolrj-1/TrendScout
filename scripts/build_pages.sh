#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/public"

rm -rf "$OUT"
mkdir -p "$OUT/dashboard" "$OUT/reports"

cp "$ROOT/dashboard/index.html" "$OUT/dashboard/index.html"
cp "$ROOT/reports/latest.json" "$OUT/reports/latest.json"
cp "$ROOT/reports/latest.md" "$OUT/reports/latest.md"

cat > "$OUT/index.html" <<'HTML'
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="refresh" content="0; url=/dashboard/">
  <link rel="canonical" href="/dashboard/">
  <title>TrendScout</title>
</head>
<body>
  <p>Opening <a href="/dashboard/">TrendScout dashboard</a>…</p>
</body>
</html>
HTML

cat > "$OUT/_headers" <<'HEADERS'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: DENY
HEADERS

echo "Cloudflare Pages output prepared at: $OUT"
