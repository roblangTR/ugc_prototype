## Brief overview

Guidelines for formatting terminal commands on macOS zsh to avoid quoting issues, interpolation errors, and syntax problems. These rules ensure commands execute correctly without triggering shell prompt errors.

## String literal quoting

- Prefer single quotes for all string literals to avoid interpolation
- Single quotes allow double quotes inside without escaping
- If a literal contains a single quote, use POSIX escape sequence: `'"'"'`
- Example: `'He said "don'"'"'t"'` (close quote, escaped quote, reopen quote)

## HTTP and JSON requests

- Use single quotes for outer wrapping, allowing JSON double quotes inside unescaped
- Example:
  ```bash
  curl -X POST 'https://example.com/api' \
    -H 'Content-Type: application/json' \
    -d '{"name":"Alice","note":"He said \"hello\""}'
  ```
- Do NOT wrap the entire `-d` payload in double quotes

## Multi-line content and heredocs

- Use single-quoted heredocs for multi-line content to avoid all interpolation
- Pattern: `command <<'DELIMITER' ... DELIMITER`
- Example:
  ```bash
  sudo tee /etc/config.json >/dev/null <<'JSON'
  {
    "token": "abc\"123",
    "path": "/Users/alice/Library/Application Support/My App"
  }
  JSON
  ```
- Prefer heredocs over `echo "multiline" > file`

## Command construction rules

- Only send commands with balanced quotes and no stray backslashes
- Join multi-step actions with `&&`, not loose newlines
- Example: `mkdir -p myproj && cd myproj && npm init -y`
- Avoid trailing backslashes unless deliberately escaping newline in heredoc

## Variable expansion

- Only use double quotes when variable expansion is needed
- Isolate the expansion portion:
  ```bash
  name="Alice"
  printf '%s\n' "Hello, $name"     # expansion needed
  printf '%s\n' 'Literal "quotes"' # no expansion
  ```

## File operations

- Create/overwrite file: `cat > path/to/file <<'EOF' ... EOF`
- With sudo: `sudo tee /path/to/file >/dev/null <<'EOF' ... EOF`
- Paths with spaces: quote the whole path with single quotes
- Example: `open '/Applications/Visual Studio Code.app'`

## macOS-specific considerations

- BSD sed requires `-i ''` for in-place edits
- Quote sed programs with single quotes:
  ```bash
  sed -i '' 's/"name": *".*"/"name": "Alice"/' config.json
  ```

## Safe script creation pattern

```bash
cat > script.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
echo 'This has "double quotes" and '"'"'single quotes'"'"' safely.'
SH
chmod +x script.sh && ./script.sh
