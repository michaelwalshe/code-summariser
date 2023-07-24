import argparse
import logging
from itertools import chain
import timeit
from pathlib import Path

import dotenv

from codesummariser.config import (
    SEARCH_DIRS,
    CODE_EXTS,
    MODEL,
    MAX_TOKENS,
    MODEL_TEMPERATURE,
    COST_PER_1K_TOKENS,
    SUMMARY_CSV,
)
from codesummariser.logger_config import setup_logger, clean_up_handlers
from codesummariser.summarise import get_summaries, check_cost


def main():
    assert dotenv.load_dotenv(), "Could not find a .env file"

    logger = setup_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=SEARCH_DIRS,
        type=lambda d: Path(d).resolve(),
        help=(
            "Which directories to search for code files. "
            f"Can be multiple, will default to: {SEARCH_DIRS}"
        ),
    )
    parser.add_argument(
        "--code-exts",
        nargs="+",
        default=CODE_EXTS,
        help=(
            "Which code extensions to search for. "
            f"Can be multiple, will default to: {CODE_EXTS}"
        ),
    )
    parser.add_argument(
        "--summary-store",
        action="store",
        default=SUMMARY_CSV,
        type=Path,
        help=f"Where to store the code summary CSV, defaults to {SUMMARY_CSV}",
    )
    parser.add_argument(
        "--model",
        default=MODEL,
        help=f"Which OpenAI model to use, defaults to: {MODEL}",
    )
    parser.add_argument(
        "--max-tokens",
        default=MAX_TOKENS,
        type=int,
        help=f"Max tokens to pass to the LLM in one chunk, defaults to: {MAX_TOKENS}",
    )
    parser.add_argument(
        "--model-temperature",
        default=MODEL_TEMPERATURE,
        type=float,
        help="How deterministic is the model?",
    )
    parser.add_argument(
        "--cost-per-1k-tokens",
        default=COST_PER_1K_TOKENS,
        type=float,
        help="How much does the model cost?",
    )
    parser.add_argument(
        "--always-check-existing-summaries",
        action="store_true",
        help=(
            "codesummariser will check if there is an existing CSV in the"
            " summary-store location. If this flag is set, it will error"
            " if that store does not exist."
        ),
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Whether to search --search-dirs recursively",
    )

    args = parser.parse_args()

    logging.info(f"Running codesummariser with args: {args}")

    # Collect all the code, split by extension
    code_paths = {ext: [] for ext in args.code_exts}
    for rootdir in args.search_dirs:
        if args.recursive:
            glob = rootdir.rglob
        else:
            glob = rootdir.glob
        for p in glob("*"):
            p = p.resolve()
            if p.suffix in code_paths:
                code_paths[p.suffix].append(p)

    # Combine the above, for alternative uses
    all_code_paths = list(chain.from_iterable(code_paths.values()))
    logging.info(
        f"Checking {len(all_code_paths)} code files in {len(args.search_dirs)} directories"
    )

    check_cost(all_code_paths, args.cost_per_1k_tokens)

    logging.info("Started codesummariser...")
    start_time = timeit.default_timer()

    for ext, paths in code_paths.items():
        get_summaries(
            code_paths=paths,
            code_ext=ext,
            summary_store=args.summary_store,
            always_check_existing_summaries=args.always_check_existing_summaries,
            model=args.model,
            model_temperature=args.model_temperature,
            max_tokens=args.max_tokens,
        )

    logging.info(
        "Finished codesummariser main process in: "
        f"{round(timeit.default_timer() - start_time)} s"
    )
    clean_up_handlers(logger)


if __name__ == "__main__":
    raise SystemExit(main())
