# Odoo Service Management Workflow

## Two-Repo Workflow

You now have two Odoo checkouts available in this Codex workspace:

- Custom codebase: `/Users/liong/Documents/Code/18_teds`
- Odoo core/reference codebase: `/Users/liong/Documents/odoo18`

### Default Rule

- Make edits in `/Users/liong/Documents/Code/18_teds` unless you explicitly ask me to change the core repo.
- Treat `/Users/liong/Documents/odoo18` as read-only reference by default.
- This is especially important because `/Users/liong/Documents/odoo18` already has local modifications.

### How To Ask For Work

- For custom module changes, mention the custom repo path or the module name.
- For core comparisons, ask me to compare a file in `18_teds` against the matching file in `odoo18`.
- If a task needs both repos, I’ll separate the changes clearly by path so you can see what belongs where.

### Handy Commands

```bash
git -C /Users/liong/Documents/Code/18_teds status --short --branch
git -C /Users/liong/Documents/odoo18 status --short --branch
git -C /Users/liong/Documents/Code/18_teds diff -- path/to/file
git -C /Users/liong/Documents/odoo18 diff -- path/to/file
rg -n "pattern" /Users/liong/Documents/Code/18_teds
rg -n "pattern" /Users/liong/Documents/odoo18
```

### Suggested Workflow

1. Inspect the Odoo core file in `/Users/liong/Documents/odoo18` if you need the upstream behavior.
2. Implement the actual change in `/Users/liong/Documents/Code/18_teds`.
3. Verify only the custom repo unless the task explicitly includes a core change.
4. If a change depends on core behavior, keep the core repo as a reference and copy only the relevant logic into the custom module.

## Setup
1. Make the manager script executable (if not already):
   ```bash
   chmod +x ~/odoo_manager.sh
   ```

2. Add alias to your `~/.zshrc` for easier access:
   ```bash
   echo "alias odoo='~/odoo_manager.sh'" >> ~/.zshrc
   source ~/.zshrc
   ```

## Available Commands

### Start Odoo (foreground)
```bash
odoo start
```
- Starts Odoo in the current terminal
- Press `Ctrl+C` to stop

### Stop Odoo
```bash
odoo stop
```
- Gracefully stops any running Odoo instance
- Uses force stop if necessary

### Restart Odoo (runs in background)
```bash
odoo restart
```
1. Stops any running Odoo instance
2. Starts Odoo in the background
3. Logs output to `~/odoo.log`

### Check Logs
```bash
tail -f ~/odoo.log
```
- View live log output
- Press `Ctrl+C` to exit

## Workflow Example

1. Start development:
   ```bash
   cd ~/Documents/Code/18_teds
   odoo start
   ```

2. After making code changes, restart:
   ```bash
   odoo restart
   ```

3. To stop when done:
   ```bash
   odoo stop
   ```
