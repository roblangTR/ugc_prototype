## Brief overview

Guidelines for formatting git commit commands to avoid shell quoting issues. These rules ensure clean, properly formatted commits without syntax errors.

## Git commit formatting

- Never wrap multi-line text or text containing double quotes in double quotes
- Use `git commit -m $'...'` syntax with `\n` for newlines when creating multi-line commit messages
- For long commit bodies or messages with mixed quotes, use single-quoted heredoc syntax: `git commit -F - <<'EOF' ... EOF`
- Always ensure quotes are balanced before executing any git commit command
- Prefer single quotes for string literals to avoid escaping issues
- Test complex commit messages with echo first if uncertain about quoting

## Examples

**Multi-line commit with newlines:**
```bash
git commit -m $'feat(module): Add new feature\n\n- Detail 1\n- Detail 2\n\nCloses #123'
```

**Long commit with heredoc:**
```bash
git commit -F - <<'EOF'
feat(module): Add comprehensive feature

- Implemented feature A
- Added feature B
- Updated documentation

This commit includes multiple changes that improve
the overall functionality.

Closes #123
EOF
```

**Simple single-line commit:**
```bash
git commit -m 'fix(bug): Resolve issue with quotes'
