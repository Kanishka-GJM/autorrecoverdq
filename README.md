# AutoRecoverDQ — Phase 1

**Autonomous Data Quality Recovery Engine**
Phase 1: Foundational ETL + Data Quality Logging (no auto-correction yet)

## What this phase does

1. Reads a raw CSV file from `data/raw/`.
2. Validates it for:
   - Missing values
   - Duplicate rows
   - Invalid date formats (any column with "date" in its name)
   - Empty strings in mandatory fields (all columns, for now)
3. Logs every detected error into a SQLite database (`logs/error_logs.db`,
   table `error_logs`).
4. Saves an unmodified copy of the dataset into `data/processed/`
   (auto-correction comes in a later phase).
5. Prints a summary of what was found.

## Folder structure

```
autorrecoverdq/
├── data/
│   ├── raw/          <- put your input CSVs here
│   └── processed/    <- output lands here
├── logs/              <- error_logs.db is created here
├── src/
│   ├── ingest.py
│   ├── validator.py
│   ├── logger.py
│   ├── database.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Setup

```bash
cd autorrecoverdq
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run

Place a CSV in `data/raw/` (a sample `orders.csv` with intentional
errors is already included), then run:

```bash
python src/main.py orders.csv
```

Example output:

```
--- AutoRecoverDQ: Processing Summary ---
File processed: orders.csv
Rows processed: 10
Missing values: 4
Duplicate rows: 0
Invalid dates: 2
Empty strings: 1
Errors logged: 7
------------------------------------------
```

## Inspecting logged errors

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('logs/error_logs.db')
for row in conn.execute('SELECT * FROM error_logs'):
    print(row)
"
```

## What's NOT in Phase 1

On purpose, this phase does **not** include:
- Automatic error correction
- An error pattern library
- Airflow / Docker
- APIs or dashboards
- Machine learning / clustering

These are planned for later phases, building on this foundation.
