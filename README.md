DevSecOps Security Pipeline

A production-style DevSecOps CI/CD pipeline for a containerized Flask application. The project integrates automated security checks into GitHub Actions and uses AWS services and modern supply-chain security practices to prevent insecure code and images from reaching the protected main branch.

🔐 Security Architecture

Developer
   │
   ▼
Pull Request / Push
   │
   ▼
GitHub Actions
   │
   ├── Bandit (SAST)
   ├── pip-audit (Dependency Security)
   ├── Trivy Filesystem Scan
   ├── Docker Build
   ├── Trivy Container Scan
   ├── AWS OIDC Authentication
   ├── ECR Scan-on-Push
   ├── OWASP ZAP (DAST)
   └── Cosign Keyless Image Signing
           │
           ▼
      Security Checks
           │
      ┌────┴────┐
      │  PASS   │
      └────┬────┘
           ▼
     Protected main

🛡️ Security Controls

1. Bandit — SAST

Bandit performs static security analysis of the Python source code.

bandit -r . -x ./.venv -ll

The pipeline fails when medium or higher severity Bandit findings are detected.

2. pip-audit — Dependency Security

pip-audit checks Python dependencies for known vulnerabilities.

pip-audit

3. Trivy Filesystem Scan

Trivy scans the repository filesystem for critical and high-severity vulnerabilities.

Severity: CRITICAL,HIGH

Unfixed vulnerabilities are ignored

exit-code: 1 makes the scan a pipeline gate

4. Trivy Container Scan

After building the Docker image, Trivy scans the container image before it is pushed to Amazon ECR.

devsecops-app:latest

Critical and high-severity findings can fail the pipeline.

5. OWASP ZAP DAST

The application is started inside a Docker container and scanned dynamically with OWASP ZAP.

http://localhost:5001

ZAP is configured as a pipeline security gate.

A verified false-positive rule is maintained in:

.zap/rules.tsv

6. AWS ECR Scan-on-Push

Amazon ECR is configured to automatically scan images when they are pushed.

The workflow also verifies the repository's image scanning configuration.

7. GitHub OIDC

GitHub Actions authenticates to AWS using OpenID Connect instead of storing long-lived AWS access keys in GitHub Secrets.

The workflow assumes the dedicated IAM role:

GitHubActions-ECR-DevSecOps

8. Cosign Keyless Signing

Container images are signed using Sigstore Cosign with keyless OIDC-based signing.

This provides image provenance and helps establish trust in the container artifact without managing a long-lived private signing key.

9. Branch Protection

The main branch requires the GitHub Actions security check to pass before a pull request can be merged.

This makes the security pipeline an enforced policy rather than an optional check.

⚙️ CI/CD Pipeline

The GitHub Actions workflow performs the following sequence:

Checkout source code

Set up Python

Install dependencies

Run pip-audit

Run Bandit SAST

Run Trivy filesystem scan

Build Docker image

Run Trivy container scan

Validate GitHub OIDC

Authenticate to AWS

Verify AWS identity

Verify ECR scan-on-push

Login to Amazon ECR

Tag Docker image

Push image to ECR

Start application for DAST

Run OWASP ZAP

Install Cosign

Sign the container image

Clean up the application container

🐳 Application

The application is a lightweight Flask service exposing:

Endpoint

Purpose

/

Application response

/health

Health check used by the CI/CD pipeline

The application listens on port 5001.

Example local run:

docker build -t devsecops-app:latest .

docker run -d   --name devsecops-test   -p 5001:5001   devsecops-app:latest

Health check:

curl http://localhost:5001/health

🔒 HTTP Security Headers

The Flask application implements several security headers, including:

X-Frame-Options

X-Content-Type-Options

Content-Security-Policy

Permissions-Policy

Cross-Origin-Embedder-Policy

Cross-Origin-Opener-Policy

Cross-Origin-Resource-Policy

Cache-Control

Pragma

Expires

These headers reduce common browser-side security risks and are also validated by the DAST stage.

☁️ AWS Infrastructure

The project uses:

Amazon ECR — Container image registry

AWS IAM — Access control

AWS STS — Temporary credentials through OIDC

GitHub OIDC — Keyless authentication from GitHub Actions

Configured AWS region:

ap-south-1

ECR repository:

devsecops-app

📁 Project Structure

devsecops-pipeline/
├── .github/
│   └── workflows/
│       └── security-pipeline.yml
├── .zap/
│   └── rules.tsv
├── .trivyignore
├── Dockerfile
├── app.py
├── requirements.txt
└── README.md

🚀 Running the Pipeline

The pipeline runs automatically on:

Pushes to main

Pull requests targeting main

Workflow:

.github/workflows/security-pipeline.yml

For pull requests, the Security Checks job must pass before merging into the protected main branch.

🎯 Project Goals

This project demonstrates how security can be integrated throughout the software delivery lifecycle rather than being performed only after deployment.

It covers:

Secure source-code development

Dependency vulnerability detection

Container vulnerability scanning

Dynamic application security testing

Cloud-native authentication

Container image scanning

Artifact signing

CI/CD security gates

Protected production branches

🧰 Technology Stack

Category

Technology

Application

Python / Flask

CI/CD

GitHub Actions

SAST

Bandit

Dependency Scan

pip-audit

Filesystem & Container Scan

Trivy

DAST

OWASP ZAP

Containerization

Docker

Registry

Amazon ECR

Cloud Authentication

GitHub OIDC / AWS IAM

Image Signing

Sigstore Cosign

Cloud

AWS

✅ Security Gate Philosophy

The core principle of this project is:

A security check should not merely report a vulnerability — it should be capable of preventing an insecure artifact from progressing through the delivery pipeline.

The protected main branch and required Security Checks status enforce this principle at the merge stage.

👨‍💻 Project

DevSecOps Security Pipeline

Built to demonstrate an end-to-end DevSecOps workflow combining application security, container security, cloud security, software supply-chain security, and CI/CD policy enforcement.
