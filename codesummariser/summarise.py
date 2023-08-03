import logging
from pathlib import Path
from typing import Dict, List

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
    SUMMARY_CSV,
    MODEL,
    CODE_SUMMARY_PROMPT,
    EXT_MAP,
)
from codesummariser.io import safe_write_code_summary_csv, read_code_summary_csv
from codesummariser.filesummary import FileSummary


def get_text_splitter(
    ext: str, ext_map: Dict[str, str] = EXT_MAP, **kwargs
) -> RecursiveCharacterTextSplitter:
    """Returns a text splitter for the given file extension.

    Args:
        ext: The extension of the code file
        ext_map: A dictionary of extensions to the full code language

    Returns:
        A LangChain RecursiveCharacterTextSplitter for that language
    """

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
            "\norder by ",
            *line_separators,
        ]
        return RecursiveCharacterTextSplitter(separators=separators, **kwargs)
    elif ext in ext_map:
        return RecursiveCharacterTextSplitter.from_language(
            Language(ext_map[ext]), **kwargs
        )
    else:
        raise ValueError(f"Unknown extension {ext}")


def count_tokens(text: str, model: str = MODEL) -> int:
    """Returns the number of tokens in the given text.

    Args:
        text (str): The text string
        model (str, optional): Which model to embed for. Defaults to MODEL.

    Returns:
        int: The number of tokens
    """
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    num_tokens = len(tokens)
    return num_tokens


def check_cost(code_paths: List[Path], cost_per_1k: int = COST_PER_1K_TOKENS) -> None:
    """Determine an expected cost of passing all code to an LLM, based on the
    number of tokens after tokenising with tiktoken. Print this info,
    and check that the user still wants to continue!

    Args:
        code_paths: A list of all code files (as path objects)
        cost_per_1k: The cost of running the model on 1000 tokens

    Raises:
        SystemExit: _description_
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
    code_paths: List[Path],
    code_ext: str = ".py",
    summary_store: Path = SUMMARY_CSV,
    always_check_existing_summaries: bool = False,
    model: str = MODEL,
    model_temperature: float = MODEL_TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> None:
    """Ask LLM to summarise each code file. If the file has already been summarised,
    then use that. For files that are too large, it will summarise each chunk, and the
    summarise the summaries.

    Args:
        code_paths (list[Path]): The paths to read code from, all should be the same
            file extension
        code_ext (str, optional): The file extension of the code. Defaults to ".py".
        summary_store (Path, optional): Where to save or append the summary to.
            Defaults to SUMMARY_CSV.
        always_check_existing_summaries (bool, optional): Whether to error if
            an existing summary is not found. Defaults to False.
        model (str, optional): Which AI model to use. Defaults to MODEL.
        model_temperature (float, optional): The predictability of the model.
            Defaults to MODEL_TEMPERATURE.
        max_tokens (int, optional): The total number of tokens that MODEL can accept
            at once. Defaults to MAX_TOKENS.

    Raises:
        FileNotFoundError: If summary_store does not exist and
            always_check_existing_summaries is set

    Returns:
        dict[Path, FileSummary]: _description_
    """
    if not all(p.suffix == code_ext for p in code_paths):
        raise ValueError(
            f"Not extensions in code_paths equal {code_ext=}: {code_paths=}"
        )

    # Create LLM for the model used
    if model.startswith("gpt"):
        logging.info(
            f"Using a chat model: {model}, this may be slower but can be cheaper"
        )
        llm = ChatOpenAI(model=model, temperature=model_temperature)
    else:
        logging.info("Using a standard LLM model")
        llm = OpenAI(model=model, temperature=model_temperature)

    # Create the summariser for this llm
    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=CODE_SUMMARY_PROMPT.partial(lang=EXT_MAP[code_ext]),
        combine_prompt=COMBINE_SUMMARY_PROMPT,
    )

    # Are there existing summaries to check?
    logging.info(
        f"Will check before summarising against existing summaries in {summary_store}"
    )
    if not summary_store.exists():
        if always_check_existing_summaries:
            raise FileNotFoundError(
                f"Couldn't find {summary_store=} and "
                f"had {always_check_existing_summaries=}"
            )
        else:
            existing_summaries = None
    else:
        existing_summaries = read_code_summary_csv(summary_store)

    # Summarise all files...
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

        code_file.summary = summary_chain.run(code_chunks).strip()
        logging.info(f"Summary for {path} is:\n{code_file.summary}\n")
        logging.info(f"Writing summaries to {summary_store}")
        safe_write_code_summary_csv(code_file, summary_store)
