import argparse
import datetime
import json
import urllib.error
import urllib.request
from pathlib import Path


def parse_track_file(filepath: Path) -> list[int]:
    track_ids = []
    if not filepath.exists():
        print(f"Error: Track ID file not found at {filepath}")
        return track_ids

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            # Ignore empty lines and comments
            if not line or line.startswith("#"):
                continue

            try:
                track_id = int(line)
                track_ids.append(track_id)
            except ValueError:
                print(f"Warning: Skipping invalid track ID '{line}'")
    return track_ids


def download_track(api_url: str, track_id: int) -> bool:
    url = f"{api_url.rstrip('/')}/api/download"
    data = json.dumps({"track-id": track_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode("utf-8"))
            print(
                f"[SUCCESS] Track {track_id}: {data.get('message')} ({data.get('filepath')})"
            )
            return True
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode("utf-8"))
            msg = error_data.get("message", e.reason)
        except Exception:
            msg = e.reason
        print(f"[FAILED]  Track {track_id} (HTTP {e.code}): {msg}")
        return False
    except urllib.error.URLError as e:
        print(f"[ERROR]   Could not connect to API server at {url}: {e.reason}")
        return False
    except Exception as e:
        print(f"[ERROR]   Unexpected error for track {track_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Batch download Deezer tracks via the Music Manager API."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to text file containing track IDs",
    )
    parser.add_argument(
        "failed",
        nargs="?",
        type=Path,
        default="failed.tracks",
        help="Path to text file that stores track IDs of failed downloads (default: failed.tracks)",
    )
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Music Manager API server base URL (default: http://127.0.0.1:8000)",
    )

    args = parser.parse_args()

    track_ids = parse_track_file(args.file)
    if not track_ids:
        print("No valid track IDs found to download.")
        return

    print(
        f"Found {len(track_ids)} track(s) to process. Sending requests to {args.api_url}...\n"
    )
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(args.failed, "a") as f:
        f.write(f"# {timestamp}\n")

    failed_count = 0
    for track_id in track_ids:
        success = download_track(args.api_url, track_id)
        if not success:
            failed_count += 1
            try:
                with open(args.failed, "a") as f:
                    f.write(f"{track_id}\n")
            except Exception as e:
                print(f"Error writing failed track ID {track_id} to {args.failed}: {e}")

    if failed_count > 0:
        print(
            f"\nProcessed with errors: {failed_count} failed track ID(s) logged to {args.failed}"
        )
    else:
        print("\nAll tracks processed successfully!")


if __name__ == "__main__":
    main()
