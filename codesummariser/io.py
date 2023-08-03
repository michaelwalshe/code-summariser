import csv
from pathlib import Path
from typing import Iterable, Dict, List

from codesummariser.filesummary import FileSummary


def read_code_summary_csv(file: Path) -> Dict[Path, FileSummary]:
    """Reads a CSV file of code summaries, and parse it in to a dictionary
    for easy checking

    Args:
        file (Path): File to read in

    Returns:
        dict[Path, FileSummary]: A dictionary of the paths to the FileSummary of that Path
    """
    summary_dict = {}
    with file.open() as f:
        r = csv.reader(f)
        next(r)
        for path, summary, contents_hash in r:
            path = Path(path)
            summary_dict[path] = FileSummary(path, summary, contents_hash)
    return summary_dict


def safe_write_code_summary_csv(
    summary: FileSummary | Iterable[FileSummary], file: Path
) -> None:
    """Writes a CSV file of code summaries.

    Args:
        summary (FileSummary | Iterable[FileSummary]): All summaries to write to file
        file (Path): The file to write to

    Raises:
        ValueError: If the columns in the CSV have changes
    """
    summary = summary if not isinstance(summary, FileSummary) else [summary]

    # If no summary already exists, then just write to disk
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        write_summary_csv(summary, file)

    # Otherwise, check that the file that exists is the right shape
    with file.open("r") as f:
        file_cols = next(csv.reader(f))
    new_cols = next(iter(summary)).field_names()
    if new_cols != file_cols:
        raise ValueError(
            "Columns have changed between the saved and new "
            f"summary CSVs, expected: {file_cols} and got {new_cols}"
        )

    # Assuming all checks passed, append to the file
    write_summary_csv(summary, file, mode="a", header=False)


def write_summary_csv(
    summary: FileSummary | Iterable[FileSummary],
    file: Path,
    mode: str = "w",
    header: bool = True,
) -> None:
    """Write FileSummarys to CSV

    Args:
        summary (FileSummary | Iterable[FileSummary]): All summaries to write to file
        file (Path): The file to write to
        mode (str, optional): What mode to open the file in. Defaults to "w".
        header (bool, optional): Whether to write a header row to file.
            Defaults to True.
    """
    summary = summary if not isinstance(summary, FileSummary) else [summary]
    with file.open(mode, newline="") as f:
        w = csv.writer(f)
        if header:
            w.writerow(summary[0].field_names())
        w.writerows(summary)
