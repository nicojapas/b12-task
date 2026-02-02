import json
import hmac
import hashlib
import os
import sys
from datetime import datetime, timezone

import requests

URL = "https://b12.io/apply/submission"
SIGNING_SECRET = os.environ.get("B12_SIGNING_SECRET")
SUBMISSION_TYPE = os.environ.get("SUBMISSION_TYPE")

if not SIGNING_SECRET:
    raise EnvironmentError("Signing Secret variable not found.")

is_example_mode = SUBMISSION_TYPE == "example"

if is_example_mode:
    print("--- Running in example mode ---")
    payload = {
        "timestamp": "2026-01-06T16:59:37.571Z",
        "name": "Your name",
        "email": "you@example.com",
        "resume_link": "https://pdf-or-html-or-linkedin.example.com",
        "repository_link": "https://link-to-github-or-other-forge.example.com/your/repository",
        "action_run_link": "https://link-to-github-or-another-forge.example.com/your/repository/actions/runs/run_id",
    }
else:
    action_run_link = os.environ.get("GITHUB_RUN_URL")
    if not action_run_link:
        print("ERROR: GITHUB_RUN_URL environment variable not found for real submission.", file=sys.stderr)
        sys.exit(1)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "name": "Nicolas Japas",
        "email": "nicolasjapas@gmail.com",
        "resume_link": "https://github.com/nicojapas/cv/blob/7a052fe45727110962de7d9a4a27b95d5290f645/Nicol%C3%A1s_Japas_CV.pdf",
        "repository_link": "https://github.com/nicojapas/b12-task",
        "action_run_link": action_run_link,
    }

body = json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")

signature = hmac.new(
    SIGNING_SECRET.encode("utf-8"),
    body,
    hashlib.sha256,
).hexdigest()

if is_example_mode:
    expected_signature = "c5db257a56e3c258ec1162459c9a295280871269f4cf70146d2c9f1b52671d45"
    print(f"Calculated signature: {signature}")
    print(f"Expected signature:   {expected_signature}")
    if signature != expected_signature:
        print("\nERROR: Signature does not match the example!", file=sys.stderr)
        sys.exit(1)
    print("Signature matches the example. Proceeding to POST.")

headers = {
    "Content-Type": "application/json; charset=utf-8",
    "X-Signature-256": f"sha256={signature}",
}

response = requests.post(URL, data=body, headers=headers, timeout=10)
response.raise_for_status()

data = response.json()
receipt = data.get("receipt")

if not receipt:
    print("No receipt returned:", data)
    sys.exit(1)

print(f"Submission receipt: {receipt}")
