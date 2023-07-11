import argparse
import logging
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
from codesummariser.io import read_code_summary_csv, write_code_summary_csv
from codesummariser.logger_config import setup_logger, clean_up_handlers
from codesummariser.summarise import get_summaries, check_cost


def main():
    dotenv.load_dotenv()
    logger = setup_logger()
    logging.info("Started codesummariser...")
    start_time = timeit.default_timer()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--search-dirs",
        nargs="+",
        default=SEARCH_DIRS,
        type=lambda dirlist: [Path(d).resolve() for d in dirlist],
        help=f"Which directories to search for code files. Can be multiple, will default to: {SEARCH_DIRS}",
    )
    parser.add_argument(
        "--summary-store",
        action="store",
        default=SUMMARY_CSV,
        type=Path,
        help="Where to store the code summary CSV",
    )
    parser.add_argument(
        "--check-existing-summaries",
        action="store_true",
        help="Whether to check the location of --summary-store for existing summaries",
    )
    parser.add_argument(
        "--code-exts",
        nargs="+",
        default=CODE_EXTS,
        type=set,
        help=f"Which code extensions to search for. Can be multiple, will default to: {CODE_EXTS}",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Whether to search --search-dirs recursively",
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

    args = parser.parse_args()

    logging.info(f"Running codesummariser with args: {args}")

    code_paths = []
    for rootdir in args.search_dirs:
        if args.recursive:
            glob = rootdir.rglob
        else:
            glob = rootdir.glob
        code_paths.extend(p.resolve() for p in glob("*") if p.suffix in args.code_exts)

    logging.info(
        f"Checking {len(code_paths)} code files in {len(args.search_dirs)} directories"
    )

    check_cost(code_paths, args.cost_per_1k_tokens)

    if args.check_existing_summaries:
        logging.info(
            "Will check before summarising against"
            f"existing summaries in {args.summary_store}"
        )
        existing_summaries = read_code_summary_csv(args.summary_store)
    else:
        existing_summaries = None

    code_summaries = get_summaries(
        code_paths=code_paths,
        existing_summaries=existing_summaries,
        model=args.model,
        model_temperature=args.model_temperature,
        max_tokens=args.max_tokens,
    )

    logging.info(f"Writing summaries to {args.summary_store}")
    write_code_summary_csv(code_summaries, args.summary_store)

    logging.info(
        f"Finished codesummariser in: {round(timeit.default_timer() - start_time)} s"
    )
    clean_up_handlers(logger)


if __name__ == "__main__":
    raise SystemExit(main())
