# Music Manager

An API server for managing and downloading music tracks from Deezer (powered by [streamrip](https://github.com/nathom/streamrip)).

## Features

- **REST API Server**: Flask-based service offering an endpoint to trigger track downloads.
- **Download Tracking**: Tracks are indexed in a local SQLite database to prevent duplicate downloads.
- **Docker Support**: Ready-to-use Dockerfile and Docker Compose configuration.
- **Batch Processing Tool**: [Utility script](./scripts/batch_download.py) to bulk download tracks from a text file.

---

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (recommended package manager)
- Deezer ARL token (for Streamrip authentication, optional)

[Instructions on how to find your Deezer ARL token](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie)

---

## Configuration

Copy `.env.example` to `.env` and configure your settings.

---

## Installation & Running

### Local Development

1. Install dependencies using `uv`:

   ```bash
   uv sync
   ```

2. Run the Flask API server:

   ```bash
   uv run music-manager
   ```

### Using Docker

Build and run using Docker Compose:

```bash
docker compose up --build
```

---

## API Usage

### 1. Check Status

- **Endpoint:** `GET /api/status`
- **Response:**
  ```json
  { "status": "ok" }
  ```

### 2. Download Track

- **Endpoint:** `POST /api/download`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  { "track-id": 14408104 }
  ```
- **Response (success):**
  ```json
  {
    "message": "Track downloaded",
    "filepath": "/path/to/library/track.mp3"
  }
  ```
- **Response (failure):**
  ```json
  {
    "message": "Download failed for track 14408104: ..."
  }
  ```

---

## Batch Download Tool

You can batch download tracks listed in a text file (one track ID per line) using the provided script:

```bash
uv run python scripts/batch_download.py download.tracks --api-url http://127.0.0.1:8000
```

Failed downloads are written to `failed.tracks` for easy retry.
