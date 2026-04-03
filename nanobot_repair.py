import os
import requests

def check_github_connectivity():
    print("[1/2] Testing GitHub API Connectivity...")
    repo = "meekotharaccoon-cell/meeko-nerve-center"
    url = f"https://api.github.com/repos/{repo}"
    response = requests.get(url)
    if response.status_code == 200:
        print(f" -> Success: Connected to {repo}")
    else:
        print(f" -> Failed: Status {response.status_code}")

def check_secret_placeholders():
    print("\n[2/2] Checking Local Knowledge for Secret Placeholders...")
    # This checks if the variables are set in the current session
    secrets = ["os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("os.getenv("ANTHROPIC_API_KEY")")")")")")")", "X_API_KEY", "GMAIL_APP_PASSWORD"]
    for secret in secrets:
        val = os.environ.get(secret)
        if val:
            print(f" -> {secret}: PRESENT (Active)")
        else:
            print(f" -> {secret}: MISSING (Dormant)")

if __name__ == "__main__":
    check_github_connectivity()
    check_secret_placeholders()
