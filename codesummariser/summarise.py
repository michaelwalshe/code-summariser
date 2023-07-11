import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain

from codesummariser.config import (
    COMBINE_SUMMARY_PROMPT,
    COST_PER_1K_TOKENS,
    MAX_TOKENS,
    MODEL_TEMPERATURE,
    MODEL,
    CODE_SUMMARY_PROMPT,
    EXT_MAP,
)


@dataclass
class FileSummary:
    """Dataclass to store the file summaries along with general info.
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


def get_text_splitter(
    ext: str, ext_map: dict[str, str] = EXT_MAP, **kwargs
) -> RecursiveCharacterTextSplitter:
    """Returns a text splitter for the given file extension."""

    # Handle special cases first, not covered by LangChain
    line_separators = ["\n\n", "\n", " ", ""]
    if ext == ".sas":
        separators = [
            "\ndata ",
            "\nproc ",
            "\nrun ",
            "\nquit ",
            "\nif ",
            "\ndo ",
            *line_separators,
        ]
        return RecursiveCharacterTextSplitter(separators=separators, **kwargs)
    elif ext == ".R":
        separators = ["\nfunction ", "\nif ", "\nfor ", "\nwhile ", *line_separators]
        return RecursiveCharacterTextSplitter(separators=separators, **kwargs)
    elif ext == ".sql":
        separators = [
            ";",
            "\ncreate ",
            "\nselect ",
            "\nfrom ",
            "\nwhere ",
            "\ngroup by ",
            "\nhaving ",
            "\order by " * line_separators,
        ]
        return RecursiveCharacterTextSplitter(separators=separators, **kwargs)
    elif ext in ext_map:
        return RecursiveCharacterTextSplitter.from_language(
            Language(ext_map[ext], **kwargs)
        )
    else:
        raise ValueError(f"Unknown extension {ext}")


def count_tokens(text: str, model: str = MODEL) -> int:
    """Returns the number of tokens in the given text."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    return num_tokens


def check_cost(code_paths: list[Path], cost_per_1k: int = COST_PER_1K_TOKENS) -> None:
    """Determine an expected cost of passing all code to an LLM, based on the
    number of tokens after tokenising with tiktoken. Print this info,
    and check that the user still wants to continue!
    """
    total_input_tokens = sum(count_tokens(cf.read_text()) for cf in code_paths)
    likely_output_tokens = len(code_paths) * 100
    total_tokens = total_input_tokens + likely_output_tokens
    print(
        f"Total input tokens is {total_tokens}. At ${cost_per_1k}/1k prompt "
        f"tokens, and with a likely {likely_output_tokens} output tokens, the cost "
        f"of this run is ${total_tokens * cost_per_1k / 1000:.2f}"
    )
    yn = input("Do you wish to continue with summarisation? [Y]/N...  ")

    if yn.upper() != "Y":
        raise SystemExit("Code summarisation cancelled by user.")


def get_summaries(
    code_paths: list[Path],
    existing_summaries: Optional[dict[Path, FileSummary]] = None,
    model: str = MODEL,
    ext_map: dict[str, str] = EXT_MAP,
    model_temperature: float = MODEL_TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> dict[Path, FileSummary]:
    """Ask LLM to summarise each code file. If the file has already been summarised,
    then use that. For files that are too large, it will summarise each chunk, and the
    summarise the summaries.
    """
    if model.startswith("gpt"):
        logging.info("Using a chat model, this may be slower but can be cheaper")
        llm = ChatOpenAI(model=model, temperature=model_temperature)
    else:
        logging.info("Using a standard LLM model")
        llm = OpenAI(model=model, temperature=model_temperature)

    code_summaries: dict[Path, FileSummary] = {}
    for path in code_paths:
        logging.info(f"Summarising {path}")

        splitter = get_text_splitter(
            path.suffix, chunk_size=max_tokens, chunk_overlap=25
        )
        code = path.read_text()
        code_file = FileSummary(path)

        if existing_summaries and path in existing_summaries:
            old_code_file = existing_summaries[path]
            if old_code_file.contents_hash == code_file.contents_hash:
                logging.info(f"Skipping {path} as it has already been summarised.")
                continue

        code_chunks = splitter.create_documents([code])

        summary_chain = load_summarize_chain(
            llm=llm,
            chain_type="map_reduce",
            map_prompt=CODE_SUMMARY_PROMPT.partial(lang=ext_map[path.suffix]),
            combine_prompt=COMBINE_SUMMARY_PROMPT,
        )

        output = summary_chain.run(code_chunks)
        code_file.summary = output.strip()
        logging.info(
            f"Summary for {path} is:\n{code_file.summary}\nOutputting to file..."
        )
        code_summaries[path] = code_file

    return code_summaries | (existing_summaries or {})
