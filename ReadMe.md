# HINGFIN — Phase 1: Dataset Construction

**A Code-Mixed Hindi–English Stock-Market Sentiment Benchmark**

## 1. Project Overview

HINGFIN is a research project focused on building an entity-level sentiment benchmark for code-mixed Hindi–English (Hinglish) text from Indian retail-investor conversations about NSE-listed equities.

The objective is to identify the sentiment expressed toward each company mentioned in a post, rather than assigning a single sentiment label to the entire post.

HINGFIN focuses on four key properties:

- **Language:** Code-mixed Hindi–English (Hinglish), including Romanised Hindi and Devanagari.
- **Domain:** Indian financial markets and NSE-listed companies.
- **Genre:** Conversational content from retail investors.
- **Entity-level labelling:** Sentiment is labelled separately for each company mentioned in a post.

Phase 1 focuses on dataset construction, data preprocessing, language identification, entity linking, annotation, and preparation of a documented dataset release. Model training and downstream analysis are planned for Phase 2.

## 2. Project Objectives

The primary objectives of HINGFIN are:

- Build a ticker universe mapping company names, abbreviations, cashtags, hashtags, and language variants to canonical NSE symbols.
- Collect conversational financial posts from relevant public sources.
- Clean and deduplicate collected data.
- Identify Hindi–English code-mixing and calculate the Code-Mixing Index (CMI).
- Match company mentions to their corresponding NSE tickers.
- Create annotation samples for entity-level sentiment labelling.
- Measure annotator agreement and adjudicate disagreements.
- Prepare a reproducible dataset release with documentation and an entity-linking artifact.

## 3. Current Progress

The repository currently contains an initial Moneycontrol data-processing pipeline and supporting utilities.

### 3.1 Ticker Universe

- NSE equity and NIFTY input files are available.
- A ticker dictionary is present.
- A script is available to generate the ticker universe.

### 3.2 Data Collection

- A Moneycontrol scraping script is available.
- Board URL resolution utilities are present.
- Raw Moneycontrol data has been collected for the current working dataset.

### 3.3 Data Cleaning and Deduplication

- A cleaning and deduplication script is available.
- Cleaned CSV and Parquet outputs have been generated.
- Cleaning reports are available for inspecting the processing results.

### 3.4 Language Identification and Code-Mixing

- A language identification and code-mixing script is available.
- Language and CMI outputs have been generated.
- Further validation and calibration of language identification and CMI thresholds remain part of the research workflow.

### 3.5 Remaining Work

The larger HINGFIN pipeline still includes entity matching and disambiguation, annotation sample construction, sentiment annotation, inter-annotator agreement analysis, adjudication, dataset splitting, and release documentation.

The current Moneycontrol pipeline is preliminary and does not represent the completed HINGFIN benchmark.

## 4. Data Sources

The Phase 1 research plan identifies the following sources and target proportions:

| Source | Target Share | Purpose |
|---|---:|---|
| YouTube comments | Approximately 55% | Primary source of Hinglish financial discussion |
| Moneycontrol Message Board | Approximately 20% | Per-stock retail-investor discussions |
| Telegram groups and comment threads | Approximately 15% | Hinglish-rich discussions, subject to ethical and access considerations |
| Reddit | Approximately 10% | Comparator dataset representing a different conversational register |

These are planned proportions for the overall dataset. The current repository work has primarily focused on Moneycontrol.

## 5. Data Processing Pipeline

HINGFIN Phase 1 consists of nine major stages.

1. **Build the Ticker Universe:** Construct a dictionary mapping company-name variants to canonical NSE symbols.
2. **Collect Data:** Collect relevant conversational posts from the selected sources.
3. **Clean and Deduplicate:** Normalize text, filter unsuitable content, and remove duplicate or near-duplicate records.
4. **Identify Language and Code-Mixing:** Assign token-level language tags and calculate CMI scores and buckets.
5. **Entity Matching:** Identify company mentions and associate them with the appropriate NSE tickers.
6. **Build Annotation Samples:** Select gold and working annotation sets using stratified sampling.
7. **Annotate:** Assign sentiment labels and additional flags to each post–ticker pair.
8. **Agreement and Adjudication:** Measure annotation agreement and resolve disagreements.
9. **Finalise and Release:** Prepare dataset splits, entity-linking artifacts, and research documentation.

## 6. Technology Stack

The planned pipeline uses the following tools and libraries:

- Python 3.10+
- pandas
- PyArrow and Parquet
- regex
- indic-nlp-library
- datasketch for MinHash-based deduplication
- scikit-learn
- krippendorff
- Google YouTube Data API v3
- BeautifulSoup and requests
- Telethon or Pyrogram for Telegram
- PRAW for Reddit
- Doccano or Label Studio for annotation

Not every tool is necessarily used by the current scripts. Dependencies should be verified against `requirements.txt` and the actual implementation.

## 7. Setup and Installation

### Prerequisites

- Python 3.10 or newer
- Git
- The dependencies listed in `requirements.txt`

### Create a Virtual Environment

Run the following commands from the repository root.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell, activate the environment using:

```powershell
.venv\Scripts\Activate.ps1
```

## 8. Running the Current Pipeline

Run commands from the repository root unless a script specifies otherwise.

```bash
python Scripts/generate_ticker_universe.py
python Scripts/scrape_moneycontrol.py
python Scripts/clean_deduplicate_moneycontrol.py
python Scripts/language_code_mixing.py
```

These commands represent the current pipeline entry points. Check each script for required inputs, command-line arguments, API configuration, and output paths before execution.

Do not run collection jobs at scale until source access, rate limits, and output locations have been verified.

## 9. Data Storage and Privacy

Raw collected text must be kept in a private working store outside Git.

The repository should contain source code, documentation, dependency declarations, and approved artifacts rather than restricted raw research text.

Recommended practices:

- Keep raw text separate from cleaned and processed outputs.
- Do not overwrite the original raw data during preprocessing.
- Store API credentials and secrets outside version control.
- Use `.gitignore` to exclude private data, environment files, and local development artifacts.
- Review processed outputs before committing because they may still contain raw text.
- Respect platform terms, API limits, rate limits, and source-specific redistribution restrictions.
- Hash author identifiers during collection where required by the research protocol.
- Follow institutional ethics requirements for annotation and Telegram data collection.
- Review source permissions and release requirements before publishing any dataset.

**Important:** `.gitignore` does not automatically stop tracking files that Git already tracks. Previously tracked private files must be untracked separately.

## 10. Annotation Schema

The planned annotation unit is a *(post, ticker)* pair.

Each pair will receive the following labels:

| Field | Description |
|---|---|
| `sentiment` | Positive, negative, or neutral sentiment toward the target ticker |
| `is_sarcastic` | Whether the sentiment is expressed ironically |
| `is_uncertain` | Whether the annotator cannot confidently assign a label |
| `is_advice_only` | Whether the post contains only a buy/sell signal without opinion content |

A post mentioning multiple companies may generate multiple annotation items. Each company must be labelled independently.

## 11. Planned Dataset and Release

The Phase 1 research plan targets:

- Approximately 1,500 gold-set post–ticker pairs before adjudication and exclusions.
- Approximately 6,500 working-set post–ticker pairs.
- Train, validation, and test splits without overlap in post IDs.
- A companion entity-linking artifact mapping company-name variants to canonical NSE symbols.
- Annotation guidelines.
- An inter-annotator agreement and adjudication report.
- A data statement and datasheet.
- A source manifest and rehydration helper where required.
- A versioned dataset release with checksums and reproducibility information.

These are project targets, not claims that the final artifacts have already been completed.

## 12. Reproducibility

To support reproducible research, record:

- Source manifest and collection window.
- Library and tool versions.
- Language identification method.
- CMI thresholds.
- Deduplication parameters.
- Random seed used for sampling.
- Annotation and adjudication procedures.
- Repository commit corresponding to each release.

## 13. Project Scope

HINGFIN Phase 1 focuses on constructing a reliable, documented, and reproducible entity-level Hinglish financial sentiment dataset.

Model training, sentiment-analysis experiments, and downstream evaluation are planned for Phase 2.

## 14. Acknowledgements

HINGFIN is a research project focused on advancing work on code-mixed language processing, entity-level sentiment analysis, and financial NLP for Indian retail-investor discourse.
