---
configs:
- config_name: default
  data_files:
  - split: train
    path: train.jsonl
  - split: eval
    path: eval.jsonl
  - split: dpo
    path: dpo.jsonl
license: apache-2.0
tags:
- code
---

# Dataset for Zeta

This is the open dataset used to train Zeta, an edit prediction model that powers Zed's predictive coding feature. Zeta is derived from Qwen2.5-Coder-7B and predicts the developer's next code edit based on their recent programming patterns and cursor position, allowing for intelligent completion with a simple tab press.

This dataset is split into three parts:

- `train.jsonl`: Contains the training data for supervised fine-tuning.
- `dpo.jsonl`: Contains the data for the direct preference optimization.
- `eval.jsonl`: Contains the evaluation data for the Zeta dataset.

These files are generated from the markdown files in the respective directories.

## Scripts

There are several scripts to help with data processing and evaluation:

- `script/pull-predictions`: Pulls predictions from Snowflake.
- `script/verify_server.py`: Simple webserver to manually verify the predictions and adding them to the dataset.
- `script/gen-dataset`: Reads all the markdown files, validates them, and generates the dataset files.
- `script/sft.ipynb`: Jupyter notebook for supervised fine-tuning.
- `script/dpo.ipynb`: Jupyter notebook for direct preference optimization.

### Running Python Scripts

Set up Python environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install fastapi uvicorn
```

Run the verification UI:
```bash
python script/verify_server.py predictions train --trash-dir trash
```

Open http://localhost:8000 and use:
- 'G' to accept (moves to `train/`)
- 'B' to reject (moves to `trash/`)

# Labeling feedback

Set up Python environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install anthropic
```

Set Anthropic API key:
```bash
export ANTHROPIC_API_KEY=your_api_key
```

Run the `label-data` script:
```bash
python script/label-data
```

Maybe some files weren't labeled because the model didn't reply with a comma-separated list of labels:

```bash
python script/see-label-data
```