import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from .database import Database
from .downloader import Downloader, DownloadFailure, DownloadSuccess

load_dotenv()

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true")
LIBRARY_PATH = Path(os.getenv("LIBRARY_PATH") or Path.home() / "music")
DB_PATH = Path(os.getenv("DB_PATH") or LIBRARY_PATH / "downloads.db")

app = Flask(__name__)
if DEBUG:
    app.logger.setLevel(logging.DEBUG)

db = Database(DB_PATH)
dl = Downloader(LIBRARY_PATH, db)


@app.route("/api/status")
def status():
    return jsonify({"status": "ok"}), 200


@app.route("/api/download", methods=["POST"])
def download():
    data = request.get_json() or {}
    raw_track_id = data.get("track-id")

    if not raw_track_id:
        return jsonify({"message": "No track ID provided"}), 400
    try:
        track_id = int(raw_track_id)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid track ID"}), 400

    app.logger.info(f"Downloading track {track_id}")
    result = dl.download_track(track_id)

    match result:
        case DownloadFailure(message, details):
            if not result.details:
                app.logger.error(f"Download failed for track {track_id}: {message}")
            else:
                app.logger.error(
                    f"Download failed for track {track_id}: {message}\n{details}"
                )
            return jsonify({"message": f"Download failed: {message}"}), 500
        case DownloadSuccess(message, filepath, duplicate):
            if duplicate:
                app.logger.info(f"Track {track_id} already downloaded")
                return (
                    jsonify(
                        {
                            "message": "Track already downloaded",
                            "filepath": str(filepath),
                        }
                    ),
                    200,
                )

            app.logger.info(f"Track {track_id} downloaded")
            return (
                jsonify({"message": "Track downloaded", "filepath": str(filepath)}),
                200,
            )


def main():
    app.run(host=HOST, port=PORT, debug=DEBUG)


if __name__ == "__main__":
    main()
