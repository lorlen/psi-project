import atexit
from hashlib import sha256
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Optional

from psi_project.core import config
from psi_project.core.utils import Singleton


class FileManager(metaclass=Singleton):
    def __init__(self):
        config.REPO_DIR.mkdir(parents=True, exist_ok=True)
        config.FILE_DIR.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(config.METADATA_DB_PATH)
        atexit.register(self.db.close)
        self.db.row_factory = sqlite3.Row

        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                name TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                owner_address TEXT
            );

            CREATE INDEX IF NOT EXISTS metadata_hash_idx ON metadata(hash);
            CREATE INDEX IF NOT EXISTS metadata_owner_address_idx ON metadata(owner_address);
            """
        )

        # ensure there are no files without metadata
        files_in_fs = set(config.FILE_DIR.iterdir())
        files_in_db = set(
            config.FILE_DIR / r[0]
            for r in self.db.execute("SELECT name FROM metadata").fetchall()
        )

        for path in files_in_fs - files_in_db:
            path.unlink()

        names_to_remove = ",".join(
            repr(str(path)) for path in files_in_db - files_in_fs
        )
        if names_to_remove:
            self.db.execute(f"DELETE FROM metadata WHERE name IN ({names_to_remove})")
            self.db.commit()

    def add_file(
        self,
        path: Path,
        name: Optional[str] = None,
        owner_address: Optional[str] = None,
    ):
        print(name)
        name = self._sanitize_name(name) or path.name

        if (config.FILE_DIR / name).exists():
            raise ValueError("File already exists in the repository")

        shutil.copy(path, config.FILE_DIR / name)
        self.db.execute(
            "INSERT INTO metadata VALUES (?,?,?)",
            (name, sha256(path.read_bytes()).hexdigest(), owner_address),
        )
        self.db.commit()

    def retrieve_file(self, name: str, path: Path):
        name = self._sanitize_name(name)

        if path.is_dir():
            path /= name

        if not (config.FILE_DIR / name).exists():
            raise ValueError("File does not exist in the repository")

        shutil.copy(config.FILE_DIR / name, path)

    def remove_file(self, name: str):
        name = self._sanitize_name(name)
        (config.FILE_DIR / name).unlink(missing_ok=True)
        self.db.execute("DELETE FROM metadata WHERE name = ?", (name))
        self.db.commit()

    def open_file(self, name: str):
        return (config.FILE_DIR / self._sanitize_name(name)).open()

    def read_file(self, name: str):
        return (config.FILE_DIR / self._sanitize_name(name)).read_bytes()

    def list_files(self):
        return self.db.execute("SELECT * FROM metadata").fetchall()

    def get_file_metadata(self, name: str):
        return self.db.execute(
            "SELECT * FROM metadata WHERE name = ?", (name,)
        ).fetchone()

    def file_exists(self, name: str):
        return (
            self.db.execute(
                "SELECT count(*) FROM metadata WHERE name = ?", (name,)
            ).fetchone()[0]
            == 1
        )

    @staticmethod
    def _sanitize_name(name: Optional[str]):
        if name is not None:
            if os.altsep:
                name.replace(os.altsep, "")
            return name.replace(os.sep, "")
        return None
