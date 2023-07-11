from pathlib import Path

from langchain import PromptTemplate


# Root directories of code to summarise. Should be list of Path objects
SEARCH_DIRS = [Path() / "data" / "inputs"]
# All code extensions to summarise. These should be plain text files
CODE_EXTS = {".sas"}
# Which model to use. See https://platform.openai.com/docs/models for options
MODEL = "gpt-3.5-turbo"
# How much does this model cost, just used for informative estimate given to user
COST_PER_1K_TOKENS = 0.02
# How many tokens can the model accept?
MAX_TOKENS = 4096
# What model temp to use, lower temps are more deterministic
MODEL_TEMPERATURE = 0.5
# Default location to store the computed summaries
SUMMARY_CSV = Path() / "data" / "summaries" / "summary.csv"

EXT_MAP = {
    # First 3 get handled as special cases, as not covered by LangChain
    ".sas": "sas",
    ".R": "R",
    ".sql": "sql",
    # Rest of the extensions are covered by LangChain
    ".py": "python",
    ".cpp": "cpp",
    ".go": "go",
    ".java": "java",
    ".js": "javascript",
    ".php": "php",
    ".rb": "ruby",
    ".scala": "scala",
    ".md": "markdown",
    ".swift": "swift",
    ".html": "html",
}

CODE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["lang", "text"],
    template="""\
You are an expert {lang} programmer. Summarise the following {lang} code, delimited by triple backquotes.:

```{text}```

CONCISE SUMMARY:""",
)

COMBINE_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="""\
Write a concise summary of the following text, delimited by triple backquotes.

```{text}```

CONCISE SUMMARY:""",
)
