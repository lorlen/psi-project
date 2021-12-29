from hashlib import sha256
from pathlib import Path
import shutil
import sqlite3
from typing import Optional

from psi_project.core import config


class FileManager:
    def __init__(self):
        config.REPO_DIR.mkdir(parents=True, exist_ok=True)
        config.FILE_DIR.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(config.METADATA_DB_PATH)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS metadata (
                name TEXT PRIMARY KEY,
                hash TEXT NOT NULL,
                owner_address TEXT
            );

            CREATE INDEX IF NOT EXISTS metadata_hash_idx ON metadata(hash);
            CREATE INDEX IF NOT EXISTS metadata_owner_address_idx ON metadata(owner_address);
        """)

        # ensure there are no files without metadata
        files_in_fs = set(config.FILE_DIR.iterdir())
        files_in_db = set(Path(r[0]) for r in self.db.execute("SELECT name FROM metadata").fetchall())

        for path in files_in_fs - files_in_db:
            path.unlink()

        names_to_remove = ",".join(repr(str(path)) for path in files_in_db - files_in_fs)
        if names_to_remove:
            self.db.execute(f"DELETE FROM metadata WHERE name IN ({names_to_remove})")

    def add_file(self, path: Path, owner_address: Optional[str] = None):
        shutil.copy(path, config.FILE_DIR / path.name)
        self.db.execute("INSERT INTO metadata VALUES (?,?,?)", (path.name, sha256(path.read_bytes()).hexdigest(), owner_address))

    def remove_file(self, name: str):
        name = Path(name).name
        (config.FILE_DIR / name).unlink(missing_ok=True)
        self.db.execute("DELETE FROM metadata WHERE name = ?", (name))

    def open_file(self, name: str):
        return (config.FILE_DIR / Path(name).name).open()

    def read_file(self, name: str):
        return (config.FILE_DIR / Path(name).name).read_bytes()

    def list_files(self):
        return self.db.execute("SELECT * FROM metadata").fetchall()

    def get_file_metadata(self, name: str):
        return self.db.execute("SELECT * FROM metadata WHERE name = ?", (name)).fetchone()

    def file_exists(self, name: str):
        return self.db.execute("SELECT count(*) FROM metadata WHERE name = ?", (name)).fetchone()[0] == 1
