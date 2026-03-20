# code-to-txt

`code-export` is a small Python 3.10+ CLI that exports a directory tree into a single UTF-8 text file using an LLM-friendly format.

## Features

- Recursively scans a base directory.
- Ignores common build, editor, cache, and dependency directories.
- Skips configured file extensions, binary files, and files larger than 1 MB.
- Preserves relative paths and sorts files alphabetically.
- Writes a single output file using the required tagged format.

## Requirements

- Python 3.10+
- No external dependencies

## Usage

```bash
./code-export <base_path> <output_path>
```

Examples:

```bash
./code-export ./src ./exports
./code-export ./src ./exports/source_dump.txt
```

If `output_path` is a directory, the tool creates `<base_directory_name>_output.txt` inside it.

## Output format

The generated file uses this structure:

```text
<BASE_PATH>/absolute/path/to/base

<FILES>
relative/path1.py
relative/path2.py
</FILES>

<FILE: relative/path1.py>
[file contents]
</FILE>

<FILE: relative/path2.py>
[file contents]
</FILE>
```

If a file cannot be read as UTF-8, the tool inserts:

```text
[ERROR: Could not read file]
```

## Ignored content

Ignored directories:

- `.git/`
- `node_modules/`
- `venv/`
- `__pycache__/`
- `dist/`
- `build/`
- `.cache/`
- `.idea/`
- `.vscode/`

Ignored file extensions:

- `.pyc`
- `.pyo`
- `.log`
- `.lock`
- `.sqlite3`
- `.bin`
- `.exe`

The tool also skips binary files and files larger than 1 MB.
