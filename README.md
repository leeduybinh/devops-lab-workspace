# DevOps Mobile Security Scanning Lab

This repository contains a simulated Flutter project and automated security scanning pipelines using MobSF and Semgrep. The reusable workflow runs the scans and publishes the JSON reports as GitHub Actions artifacts, so it can be tested from a personal GitHub repository without any GitHub App or external vulnerability-management service.

## Project Structure

```text
devops-lab/
├── .github/
│   └── workflows/
│       ├── devops-mobile-scan-cronjob.yml# Reusable workflow running scans & uploading findings
│       └── schedule-scan.yml             # Caller workflow (runs on schedule, PRs, or manual trigger)
├── android/
│   └── app/
│       └── src/
│           └── main/
│               └── AndroidManifest.xml   # Mock vulnerable Android config (allowBackup, etc.)
├── ios/
│   └── Runner/
│       └── Info.plist                    # Mock vulnerable iOS plist (ATS bypass)
├── lib/
│   ├── main.dart                         # Entry point of the mock Flutter app
│   └── services/
│       └── api_service.dart              # Mock vulnerable service (hardcoded secrets, TLS disable)
├── pubspec.yaml                          # Dart project configuration
└── README.md                             # Documentation
```

---

## 🛠️ Implemented Features

### 1. Reusable Scanning Workflow
The workflow [`devops-mobile-scan-cronjob.yml`](file://./.github/workflows/devops-mobile-scan-cronjob.yml) provides:
* **MobSF Scan**: Executes `MobSF/mobsfscan-action` to parse Android/iOS config issues and outputs `mobsfscan.json`.
* **Semgrep Scan**: Installs and executes Semgrep CLI, specifically targeting Flutter Dart source code under the `lib/` directory using our custom ruleset.
* **GitHub Actions Artifacts**: Uploads `mobsfscan.json` and `semgrep.json` for review from the workflow run.

### 2. Pipeline Integration
The pipeline scheduler [`schedule-scan.yml`](file://./.github/workflows/schedule-scan.yml) sets up:
* **Cron Scheduling**: Configured to run every day at midnight UTC.
* **Event Triggers**: Runs on pull requests targeting `main` (for paths containing source and config files) and on published releases.
* **Manual Execution**: Supports `workflow_dispatch` through the GitHub Actions tab, with input selection for environment (`development`, `staging`, `production`).

---

## 🎯 Test Vulnerabilities (Deliberately Placed)

To ensure your scans have positive findings to upload, the repository includes:
1. **Hardcoded Secrets**: Google API keys and Database Passwords stored in [`api_service.dart`](file://./lib/services/api_service.dart#L5-L6).
2. **Bypassed TLS/SSL Verification**: Custom `badCertificateCallback` returning `true` (trust all certificates) in [`api_service.dart`](file://./lib/services/api_service.dart#L14-L16).
3. **Insecure Android Manifest**: `android:allowBackup="true"`, `android:usesCleartextTraffic="true"`, and `android:debuggable="true"` in [`AndroidManifest.xml`](file://./android/app/src/main/AndroidManifest.xml#L13-L20).
4. **App Transport Security Bypass**: iOS configurations permitting non-HTTPS connections (`NSAllowsArbitraryLoads = true`) in [`Info.plist`](file://./ios/Runner/Info.plist#L28-L31).

---

## 🚀 Testing the Pipeline in Your Repository

No repository secrets or GitHub App are required. Push this project to a GitHub repository, then run **Mobile Security Scanning Pipeline** from the Actions tab with `workflow_dispatch`.

When the workflow finishes, download the `mobsfscan-<environment>` and `semgrep-<environment>` artifacts from the run summary to inspect the scan output.
