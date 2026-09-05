import os
import sys
import base64
import httpx

GITHUB_USER = "harman-1-reddy"
REPO_NAME = "medvault-ai"
REPO_DESC = "AI-powered clinical intelligence platform for patient intake, medical report extraction, reference-range verification, conflict detection, and dual-perspective summaries."

def upload_repo(token: str):
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    print(f">>> [1/3] Creating repository '{REPO_NAME}' for user '{GITHUB_USER}'...")
    with httpx.Client(timeout=30) as client:
        # Check if repo already exists or create it
        create_payload = {
            "name": REPO_NAME,
            "description": REPO_DESC,
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False
        }
        res = client.post("https://api.github.com/user/repos", json=create_payload, headers=headers)
        if res.status_code == 201:
            print(f"    Repository created successfully: https://github.com/{GITHUB_USER}/{REPO_NAME}")
        elif res.status_code == 422:
            print(f"    Repository '{REPO_NAME}' already exists. Updating contents...")
        else:
            print(f"    Error creating repo ({res.status_code}): {res.text}")
            return False

        print(">>> [2/3] Uploading all project files to GitHub...")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Files to upload
        files_to_upload = []
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root or ".git" in root or "uploads" in root:
                continue
            for file in files:
                if file.endswith((".pyc", ".zip")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
                files_to_upload.append((full_path, rel_path))

        for full_path, rel_path in files_to_upload:
            with open(full_path, "rb") as f:
                content_bytes = f.read()
            encoded_content = base64.b64encode(content_bytes).decode("utf-8")

            # Check if file exists to obtain sha if updating
            sha = None
            check_res = client.get(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{rel_path}", headers=headers)
            if check_res.status_code == 200:
                sha = check_res.json().get("sha")

            payload = {
                "message": f"feat: add {rel_path}",
                "content": encoded_content
            }
            if sha:
                payload["sha"] = sha

            put_res = client.put(f"https://api.github.com/repos/{GITHUB_USER}/{REPO_NAME}/contents/{rel_path}", json=payload, headers=headers)
            if put_res.status_code in [200, 201]:
                print(f"    Uploaded: {rel_path}")
            else:
                print(f"    Failed {rel_path} ({put_res.status_code}): {put_res.text[:100]}")

        print("\n" + "=" * 60)
        print(f" Successfully posted MedVault AI to GitHub!")
        print(f" Repository URL: https://github.com/{GITHUB_USER}/{REPO_NAME}")
        print("=" * 60)
        return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        upload_repo(sys.argv[1])
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            upload_repo(token)
        else:
            print("Usage: python push_to_github.py <YOUR_GITHUB_PERSONAL_ACCESS_TOKEN>")
