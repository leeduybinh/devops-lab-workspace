#!/usr/bin/env python3
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "ERROR": 1,
    "MEDIUM": 2,
    "WARNING": 3,
    "LOW": 4,
    "INFO": 5,
}


def normalize_path(path):
    if not path:
        return "unknown"
    marker = "devops-lab-workspace/"
    if marker in path:
        return path.split(marker, 1)[1]
    return path


def load_json(path):
    with Path(path).open() as report:
        return json.load(report)


def semgrep_findings(data):
    findings = []
    for result in data.get("results", []):
        extra = result.get("extra", {})
        findings.append(
            {
                "scanner": "Semgrep",
                "rule": result.get("check_id", "unknown"),
                "severity": (extra.get("severity") or "INFO").upper(),
                "file": normalize_path(result.get("path")),
                "line": result.get("start", {}).get("line"),
                "message": extra.get("message", "No description provided."),
                "evidence": result.get("extra", {}).get("lines", "").strip(),
                "reference": "",
            }
        )
    return findings


def mobsf_findings(data):
    findings = []
    for rule, result in data.get("results", {}).items():
        metadata = result.get("metadata", {})
        files = result.get("files", []) or [{}]
        for file_result in files:
            findings.append(
                {
                    "scanner": "MobSF",
                    "rule": rule,
                    "severity": (metadata.get("severity") or "INFO").upper(),
                    "file": normalize_path(file_result.get("file_path")),
                    "line": None,
                    "message": metadata.get("description", "No description provided."),
                    "evidence": file_result.get("match_string", ""),
                    "reference": metadata.get("reference", ""),
                }
            )
    return findings


def severity_class(severity):
    return severity.lower().replace("error", "high")


def render_finding(finding):
    line = f":{finding['line']}" if finding.get("line") else ""
    reference = ""
    if finding.get("reference"):
        ref = html.escape(finding["reference"])
        reference = f'<a class="reference" href="{ref}">Reference</a>'
    evidence = ""
    if finding.get("evidence"):
        evidence = f"<pre>{html.escape(finding['evidence'])}</pre>"
    return f"""
      <article class="finding {severity_class(finding['severity'])}">
        <div class="finding-header">
          <span class="badge {severity_class(finding['severity'])}">{html.escape(finding['severity'])}</span>
          <span class="scanner">{html.escape(finding['scanner'])}</span>
        </div>
        <h2>{html.escape(finding['rule'])}</h2>
        <p>{html.escape(finding['message'])}</p>
        <div class="meta">
          <span>{html.escape(finding['file'])}{html.escape(line)}</span>
          {reference}
        </div>
        {evidence}
      </article>
    """


def build_html(findings):
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = {}
    scanners = {}
    for finding in findings:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1
        scanners[finding["scanner"]] = scanners.get(finding["scanner"], 0) + 1

    findings = sorted(
        findings,
        key=lambda item: (
            SEVERITY_ORDER.get(item["severity"], 99),
            item["scanner"],
            item["file"],
            item["rule"],
        ),
    )

    count_cards = "\n".join(
        f"""
        <section class="stat">
          <span>{html.escape(label)}</span>
          <strong>{value}</strong>
        </section>
        """
        for label, value in [
            ("Total Findings", len(findings)),
            ("Semgrep", scanners.get("Semgrep", 0)),
            ("MobSF", scanners.get("MobSF", 0)),
            ("High/Error", counts.get("ERROR", 0) + counts.get("HIGH", 0)),
            ("Warning", counts.get("WARNING", 0)),
        ]
    )
    finding_cards = "\n".join(render_finding(finding) for finding in findings)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mobile Security Scan Report</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #5f6b7a;
      --border: #d9dee7;
      --high: #b42318;
      --warning: #a15c07;
      --info: #31527a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.5;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    header {{
      margin-bottom: 24px;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(28px, 4vw, 42px);
      line-height: 1.1;
    }}
    .subtitle {{
      margin: 0;
      color: var(--muted);
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
      margin: 24px 0;
    }}
    .stat, .finding {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }}
    .stat {{
      padding: 16px;
    }}
    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 13px;
    }}
    .stat strong {{
      display: block;
      margin-top: 6px;
      font-size: 28px;
    }}
    .finding {{
      margin: 14px 0;
      padding: 18px;
      border-left: 5px solid var(--info);
    }}
    .finding.high {{ border-left-color: var(--high); }}
    .finding.warning {{ border-left-color: var(--warning); }}
    .finding-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      height: 24px;
      padding: 0 9px;
      border-radius: 999px;
      color: #fff;
      background: var(--info);
      font-size: 12px;
      font-weight: 700;
    }}
    .badge.high {{ background: var(--high); }}
    .badge.warning {{ background: var(--warning); }}
    .scanner {{
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 18px;
      overflow-wrap: anywhere;
    }}
    p {{
      margin: 0 0 12px;
      color: #283546;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }}
    .reference {{
      color: #2457a6;
      font-family: inherit;
    }}
    pre {{
      margin: 14px 0 0;
      padding: 12px;
      overflow-x: auto;
      border-radius: 6px;
      background: #f1f3f7;
      color: #1f2937;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Mobile Security Scan Report</h1>
      <p class="subtitle">Generated from <code>semgrep.json</code> and <code>mobsfscan.json</code> at {generated_at}.</p>
    </header>
    <section class="stats">
      {count_cards}
    </section>
    <section>
      {finding_cards}
    </section>
  </main>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate an HTML report from Semgrep and MobSF JSON files.")
    parser.add_argument("--semgrep", default="semgrep.json")
    parser.add_argument("--mobsf", default="mobsfscan.json")
    parser.add_argument("--output", default="reports/security-report.html")
    args = parser.parse_args()

    findings = []
    findings.extend(semgrep_findings(load_json(args.semgrep)))
    findings.extend(mobsf_findings(load_json(args.mobsf)))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_html(findings), encoding="utf-8")
    print(f"Wrote {output} with {len(findings)} findings.")


if __name__ == "__main__":
    main()
