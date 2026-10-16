from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator, Literal

    from .database import Database

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".opus"}
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

ENV = os.environ.copy()
ENV["COLUMNS"] = "999"
ENV["TERM"] = "dumb"


@dataclass
class DownloadSuccess:
    message: str
    filepath: Path
    duplicate: bool = False


@dataclass
class DownloadFailure:
    message: str
    details: str | None = None


@dataclass
class LogRecord:
    message: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Downloader:
    def __init__(self, library_path: str | Path, db: Database | None = None):
        self.__library_path = Path(library_path)
        self.__db = db

        self.__lock = Lock()

    def download_track(self, track_id: int) -> DownloadSuccess | DownloadFailure:
        # acquiring the lock when running streamrip is on purpose, force downloads to be sequential
        # when run concurrently, streamrip has trouble with filepaths when embedding cover artwork
        with self.__lock:
            return self.__download_track(track_id)

    def __download_track(self, track_id: int) -> DownloadSuccess | DownloadFailure:
        if track_id < 0:
            return DownloadFailure("Invalid track ID")

        if self.__db:
            filename = self.__db.get(track_id)
            if filename != None:
                filepath = self.__library_path / filename
                return DownloadSuccess(
                    "Track already downloaded",
                    filepath,
                    duplicate=True,
                )

        self.__library_path.mkdir(parents=True, exist_ok=True)

        # snapshot existing files in the download folder
        prev_files = {
            f.resolve() for f in self.__library_path.glob("**/*") if f.is_file()
        }

        # download track
        stdout = subprocess.run(
            [
                "rip",
                "-f",
                self.__library_path,
                "id",
                "deezer",
                "track",
                str(track_id),
            ],
            capture_output=True,
            text=True,
            env=ENV,
        ).stdout
        logs = list(self.__parse_stdout(stdout))

        # find any newly created files
        cur_filepaths = {
            f.resolve() for f in self.__library_path.glob("**/*") if f.is_file()
        }
        new_filepaths = cur_filepaths - prev_files
        new_audio_filepaths = {
            f for f in new_filepaths if f.suffix.lower() in AUDIO_EXTENSIONS
        }

        def fail(message: str, details: str | None = None):
            for p in new_filepaths:
                p.unlink(missing_ok=True)
            return DownloadFailure(message, details)

        # check if no error messages are output
        for log in logs:
            if log.level == "ERROR":
                if re.search(r"track/\d+ no data", log.message):
                    return fail("Track not found on remote source")
                return fail("External download process failed", log.message)

        # check if any new files are created
        if len(new_audio_filepaths) == 0:
            return fail("No audio files generated")
        if len(new_audio_filepaths) > 1:
            return fail(
                "Multiple audio files generated for a single track",
                str([p.name for p in new_audio_filepaths]),
            )

        # check if audio file is not empty
        file = new_audio_filepaths.pop()
        if file.stat().st_size == 0:
            return fail("Downloaded audio file is empty", file.name)

        if self.__db:
            self.__db.set(track_id, file.name)
        return DownloadSuccess("Track downloaded", file)

    @staticmethod
    def __parse_stdout(stdout: str) -> Generator[LogRecord]:
        for line in stdout.split("\n"):
            if not line:
                continue

            # remove timestamp
            if line[0] == "[":
                line = line[11:]
            line = line.strip()

            for level in LOG_LEVELS:
                if line.startswith(level):
                    line = line[len(level) :]  # remove log level
                    # remove filename and lineno
                    line = line[: line.index(".py:")]
                    line = line[: line.rfind(" ")].strip()
                    yield LogRecord(line, level)
