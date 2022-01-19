from pathlib import Path
import logging

REPO_DIR = Path(".psi-repo")
FILE_DIR = REPO_DIR / "files"
METADATA_DB_PATH = REPO_DIR / "metadata.db"
LOG_FILE = "psi-project.log"
LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"
LOG_LEVEL = logging.DEBUG
UDP_PORT = 9000
TCP_PORT = 8888

