import time
import os
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RepoSyncHandler(FileSystemEventHandler):
    def __init__(self, api_url: str, local_repo_path: str):
        self.api_url = api_url
        self.local_repo_path = local_repo_path
        self.last_sync = 0
        self.cooldown = 10  # Wait at least 10 seconds between syncs to avoid spam
        
    def on_modified(self, event):
        if event.is_directory or ".git" in event.src_path or "__pycache__" in event.src_path:
            return
            
        current_time = time.time()
        if current_time - self.last_sync > self.cooldown:
            self.last_sync = current_time
            print(f"\n[Real-Time Sync] File changed: {event.src_path}")
            print("[Real-Time Sync] Triggering background re-index...")
            try:
                response = requests.post(
                    f"{self.api_url}/index",
                    json={"github_url": f"local:///{self.local_repo_path}"}
                )
                if response.status_code == 200:
                    print("[Real-Time Sync] Re-index successful.")
                else:
                    print(f"[Real-Time Sync] Re-index failed: {response.text}")
            except Exception as e:
                print(f"[Real-Time Sync] Failed to connect to API: {e}")

def start_watching(local_repo_path: str, api_url: str = None):
    if api_url is None:
        api_url = os.getenv("BACKEND_URL", "http://localhost:8001")

    if not os.path.exists(local_repo_path):
        print(f"Path {local_repo_path} does not exist.")
        return
        
    local_repo_path = os.path.abspath(local_repo_path)
    # Ensure paths are passed properly with forward slashes for the URI
    formatted_path = local_repo_path.replace("\\", "/")
    
    event_handler = RepoSyncHandler(api_url, formatted_path)
    observer = Observer()
    observer.schedule(event_handler, local_repo_path, recursive=True)
    observer.start()
    
    print(f"👀 Watching {local_repo_path} for changes...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python file_watcher.py <path_to_local_repo>")
        sys.exit(1)
    
    start_watching(sys.argv[1])
