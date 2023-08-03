import hashlib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import List


@dataclass
class FileSummary:
    """Dataclass to store the file summaries along with general info.

    Attributes:
        path (Path | str): Path to the file being summarised
        summary (str): A summary of the file, provided by the user
        contents_hash (str): The hash representing the file contents. Will be generated
            automatically

    Methods:
        hash_file(block_size=65536): Compute the hash of the stored file
        field_names(): Return all the names of the dataclass fields
    """

    path: Path | str
    summary: str = ""
    contents_hash: str = ""

    def __post_init__(self):
        if not isinstance(self.path, Path):
            self.path = Path(self.path)

        if not self.contents_hash:
            self.contents_hash = self.hash_file()

    def __iter__(self):
        return iter([str(self.path), self.summary, self.contents_hash])

    def hash_file(self, block_size: int = 65536) -> str:
        """Returns a hash of the file in this FileSummary"""
        file_hasher = hashlib.sha256()
        with self.path.open("rb") as f:
            file_buffer = f.read(block_size)
            while len(file_buffer) > 0:
                file_hasher.update(file_buffer)
                file_buffer = f.read(block_size)
        return file_hasher.hexdigest()

    def field_names(self) -> List[str]:
        return [f.name for f in fields(self)]
