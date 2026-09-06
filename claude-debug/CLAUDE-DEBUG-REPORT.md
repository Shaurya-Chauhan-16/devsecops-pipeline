# DevSecOps GitHub Actions → AWS OIDC Failure Investigation

## Project

GitHub repository:

Shaurya-Chauhan-16/devsecops-pipeline

Workflow:

.github/workflows/security-pipeline.yml

AWS role:

GitHubActions-ECR-DevSecOps

AWS region:

ap-south-1

The workflow is intended to authenticate to AWS using GitHub Actions OIDC and then access Amazon ECR.

---

# Current failure

GitHub Actions fails at:

Configure AWS credentials

using:

aws-actions/configure-aws-credentials@v4

The important error is:

Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity

The workflow successfully reaches the AWS credential configuration step, but AWS STS rejects the GitHub OIDC role assumption.

---

# Latest relevant GitHub run

Run ID:

33970774224

Command used:

gh run view 33970774224 --log-failed

Failure:

Could not assume role with OIDC: Not authorized to perform sts:AssumeRoleWithWebIdentity

The workflow showed:

role-to-assume:
arn:aws:iam::135330967527:role/GitHubActions-ECR-DevSecOps

aws-region:
ap-south-1

audience:
sts.amazonaws.com

---

# GitHub OIDC diagnostic results

The Debug GitHub OIDC step produced:

Repository:
Shaurya-Chauhan-16/devsecops-pipeline

Ref:
refs/heads/main

Event:
push

Workflow:
DevSecOps Security Pipeline

Actor:
Shaurya-Chauhan-16

Therefore the failing run is a normal push to the main branch.

---

# IMPORTANT: AWS trust policy changed during debugging

Originally the AWS role trust policy contained:

repo:Shaurya-Chauhan-16/devsecops-pipeline:ref:refs/heads/main

and:

repo:Shaurya-Chauhan-16/devsecops-pipeline:pull_request

However, after running:

aws iam update-assume-role-policy \
  --role-name GitHubActions-ECR-DevSecOps \
  --policy-document file://trust-policy.json

the trust policy became:

repo:Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577:ref:refs/heads/main

and:

repo:Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577:pull_request

This appears inconsistent with the actual GitHub repository OIDC subject and is highly suspicious.

The actual repository is:

Shaurya-Chauhan-16/devsecops-pipeline

The GitHub Actions diagnostic showed:

Repository: Shaurya-Chauhan-16/devsecops-pipeline

Therefore investigate this trust-policy mismatch first.

---

# Current AWS OIDC provider

Provider ARN:

arn:aws:iam::135330967527:oidc-provider/token.actions.githubusercontent.com

Provider URL:

token.actions.githubusercontent.com

Client ID:

sts.amazonaws.com

The provider was inspected with:

aws iam get-open-id-connect-provider

At one point its thumbprint was:

ab9d0263244dd0326eb67015705a667e79cfe998

It was temporarily changed to:

6938fd4d98bab03faadb97b34396831e3780aea1

and then changed back to:

ab9d0263244dd0326eb67015705a667e79cfe998

Current provider state should be checked from aws-oidc-provider.json rather than assumed from this report.

---

# TLS certificate investigation

The following was run:

openssl s_client \
  -connect token.actions.githubusercontent.com:443 \
  -servername token.actions.githubusercontent.com \
  -showcerts

TLS verification succeeded:

Verification: OK

The certificate chain was successfully retrieved.

The locally calculated SHA-1 fingerprint of the third certificate was:

AB:9D:02:63:24:4D:D0:32:6E:B6:70:15:70:5A:66:7E:79:CF:E9:98

This corresponded to:

ab9d0263244dd0326eb67015705a667e79cfe998

The provider was restored to that value.

Do not assume the thumbprint is the root cause without verifying AWS/GitHub OIDC behavior.

---

# IAM role investigation

Role ARN:

arn:aws:iam::135330967527:role/GitHubActions-ECR-DevSecOps

Role path:

/

Permissions boundary:

null

Role tags:

none

Attached permission policy:

AmazonEC2ContainerRegistryPowerUser

Inline role policies:

none

The role therefore has ECR permissions, but the current failure occurs before those permissions matter.

---

# Trust relationship originally observed

The original trust relationship was:

Principal:
arn:aws:iam::135330967527:oidc-provider/token.actions.githubusercontent.com

Action:
sts:AssumeRoleWithWebIdentity

Conditions:

StringEquals:
token.actions.githubusercontent.com:aud = sts.amazonaws.com

StringLike:
token.actions.githubusercontent.com:sub =

repo:Shaurya-Chauhan-16/devsecops-pipeline:ref:refs/heads/main

repo:Shaurya-Chauhan-16/devsecops-pipeline:pull_request

---

# Trust relationship currently observed after debugging

The currently observed policy was changed to:

repo:Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577:ref:refs/heads/main

repo:Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577:pull_request

This is likely incorrect.

Determine why trust-policy.json generated those unexpected @... values.

---

# Tests already performed

## Test 1 — GitHub workflow execution

Command:

gh run list --workflow=security-pipeline.yml --limit 2

Result:

Runs start successfully.

The latest run fails during AWS role assumption.

Conclusion:

GitHub Actions workflow itself is triggering.

---

## Test 2 — GitHub OIDC diagnostic step

Command:

grep -A20 -B5 "Debug GitHub OIDC" oidc-run.log

Result:

Repository:
Shaurya-Chauhan-16/devsecops-pipeline

Ref:
refs/heads/main

Event:
push

Conclusion:

The GitHub-side repository/ref information is what is expected for the main branch.

---

## Test 3 — AWS OIDC provider

Command:

aws iam get-open-id-connect-provider ...

Result:

URL:
token.actions.githubusercontent.com

ClientID:
sts.amazonaws.com

Thumbprint:
ab9d0263244dd0326eb67015705a667e79cfe998

Conclusion:

OIDC provider exists and has the expected audience.

---

## Test 4 — AWS role trust policy

Command:

aws iam get-role ...

Result:

The role trusts the GitHub OIDC provider and allows:

sts:AssumeRoleWithWebIdentity

However, the `sub` condition was later changed to an apparently malformed value containing:

@182733086

and:

@1358080577

This is a major suspect.

---

## Test 5 — Role permissions

Command:

aws iam list-attached-role-policies ...

Result:

AmazonEC2ContainerRegistryPowerUser

Conclusion:

The role has ECR permissions. This does NOT explain the AssumeRoleWithWebIdentity failure because authentication fails before ECR permissions are evaluated.

---

## Test 6 — Inline policies

Command:

aws iam list-role-policies ...

Result:

No inline policies.

---

## Test 7 — Permissions boundary

Command:

aws iam get-role \
  --role-name GitHubActions-ECR-DevSecOps \
  --query 'Role.PermissionsBoundary'

Result:

null

Conclusion:

No permissions boundary is restricting the role.

---

## Test 8 — IAM policy simulation

Command:

aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::135330967527:role/GitHubActions-ECR-DevSecOps \
  --action-names sts:AssumeRoleWithWebIdentity \
  --context-entries \
    ContextKeyName=token.actions.githubusercontent.com:aud,ContextKeyValues=sts.amazonaws.com,ContextKeyType=string \
    ContextKeyName=token.actions.githubusercontent.com:sub,ContextKeyValues=repo:Shaurya-Chauhan-16/devsecops-pipeline:ref:refs/heads/main,ContextKeyType=string

Result:

EvalDecision:
implicitDeny

MatchedStatements:
[]

MissingContextValues:
[]

This supports that the simulated trust relationship was not matching, but IAM policy simulation for web-identity federation may not perfectly reproduce the real STS OIDC evaluation. Treat this as supporting evidence, not the sole proof.

---

## Test 9 — Manual STS call

An attempted command was:

aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::135330967527:role/GitHubActions-ECR-DevSecOps \
  --role-session-name test \
  --web-identity-token "$(cat /dev/null)"

Result:

Invalid length for parameter WebIdentityToken, value: 0

Conclusion:

This was NOT a meaningful authentication test because no real GitHub OIDC token was supplied.

---

## Test 10 — GitHub workflow dispatch

Command:

gh workflow run security-pipeline.yml

Result:

HTTP 422:

Workflow does not have 'workflow_dispatch' trigger

Conclusion:

The workflow currently cannot be manually dispatched. Runs are currently triggered by push.

---

# Important timeline

1. GitHub workflow failed with AssumeRoleWithWebIdentity authorization error.
2. Added Debug GitHub OIDC step.
3. Confirmed GitHub repository/ref/event values.
4. Inspected AWS OIDC provider.
5. Inspected IAM role trust policy.
6. Tested OIDC certificate/thumbprint.
7. Temporarily changed OIDC thumbprint and restored it.
8. Tested IAM policy simulation.
9. Inspected role permissions and permissions boundary.
10. Updated the trust policy using trust-policy.json.
11. The resulting trust policy unexpectedly contained:
   Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577
12. Latest workflow runs still failed.

---

# What I need you to investigate

Do NOT simply regenerate a generic GitHub OIDC workflow.

First inspect:

1. security-pipeline.yml
2. trust-policy.json
3. aws-trust-policy.json
4. aws-oidc-provider.json
5. latest-run.log
6. workflow-from-github.yml
7. git history/diff

Determine:

A. Why trust-policy.json generated the malformed repository subject containing @182733086 and @1358080577.

B. What exact `sub` claim GitHub is sending for this push workflow.

C. Whether the IAM trust policy exactly matches that claim.

D. Whether the OIDC provider configuration is correct.

E. Whether repository/org/repository-variable/environment configuration affects the OIDC subject.

F. Whether the workflow's permissions include:

id-token: write

G. Whether any GitHub environment or reusable workflow changes the OIDC `sub`.

H. Whether there is an AWS account/SCP/identity restriction affecting AssumeRoleWithWebIdentity.

Do not modify AWS resources blindly. First establish the exact mismatch and then provide the minimum corrective change.

---

# Most suspicious finding

The strongest concrete anomaly discovered so far is:

GitHub reports repository:

repo:Shaurya-Chauhan-16/devsecops-pipeline

but the current IAM trust condition was changed to:

repo:Shaurya-Chauhan-16@182733086/devsecops-pipeline@1358080577:...

These values do not match.

