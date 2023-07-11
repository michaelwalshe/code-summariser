import csv
from pathlib import Path

from codesummariser.summarise import FileSummary


def read_code_summary_csv(file: Path) -> dict[Path, FileSummary]:
    """Reads a CSV file of code summaries."""
    summary_dict = {}
    with file.open() as f:
        r = csv.reader(f)
        next(r)
        for path, summary, contents_hash in r:
            path = Path(path)
            summary_dict[path] = FileSummary(path, summary, contents_hash)
    return summary_dict


def write_code_summary_csv(summary_dict: dict[Path, FileSummary], file: Path) -> None:
    """Reads a CSV file of code summaries."""
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)

    file_summaries = list(summary_dict.values())
    with file.open("w", newline="") as f:
        w = csv.writer(f)
        fieldnames = file_summaries[0].__dataclass_fields__.keys()
        w.writerow(fieldnames)
        w.writerows(file_summaries)
