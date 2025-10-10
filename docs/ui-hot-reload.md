# UI Hot Reload

The Elastic News UI now includes hot reload support for faster development.

## What is Hot Reload?

Hot reload automatically restarts the UI server whenever you save changes to Python files in the `ui/` directory. This means:

- ✅ No need to manually restart the UI after code changes
- ✅ Changes appear in browser after refresh
- ✅ Faster development iteration
- ✅ Works for all UI files (pages, services, state, etc.)

## Usage

### Standalone UI (Always Hot Reload)

```bash
./start_ui.sh
```

The standalone UI script **always** starts with hot reload enabled by default.

### UI with Agents

```bash
# Without hot reload
./start_newsroom.sh --with-ui

# With hot reload (agents + UI)
./start_newsroom.sh --with-ui --reload
```

When you use `--reload` flag:
- **Agents** reload when their code changes
- **UI** also reloads when UI code changes

## What Gets Reloaded?

### UI Files (Always with `./start_ui.sh`)
- `ui/main.py`
- `ui/pages/*.py` (home.py, article.py)
- `ui/services/*.py` (news_chief_client.py)
- `ui/state/*.py` (app_state.py)
- `ui/components/*.py` (future components)

### Agent Files (Only with `--reload` flag)
- `agents/*.py` (all agent files)

## Development Workflow

### Typical Development Session

1. **Start everything with hot reload:**
   ```bash
   ./start_newsroom.sh --with-ui --reload
   ```

2. **Make changes to UI code:**
   - Edit `ui/pages/home.py`
   - Save file
   - Mesop detects change and reloads UI
   - Refresh browser to see changes

3. **Make changes to agent code:**
   - Edit `agents/news_chief.py`
   - Save file
   - Uvicorn detects change and reloads agent
   - Agent automatically reconnects

### UI-Only Development

If you're only working on the UI and agents are already running:

1. **Start agents once:**
   ```bash
   ./start_newsroom.sh
   ```

2. **Start UI with hot reload:**
   ```bash
   ./start_ui.sh
   ```

3. **Edit UI code:**
   - Changes reload automatically
   - Agents keep running without interruption

## Logs

Hot reload events appear in logs:

```
2025-10-09 12:30:00 - INFO - Detected file change in ui/pages/home.py
2025-10-09 12:30:01 - INFO - Reloading...
2025-10-09 12:30:02 - INFO - UI restarted successfully
```

View logs:
```bash
tail -f logs/UI.log
```

## Technical Details

### Mesop Hot Reload

Mesop uses its built-in `--reload` flag which:
- Watches all Python files in the UI directory
- Detects changes using file system watchers
- Automatically restarts the Mesop server
- Preserves server configuration (port, etc.)

### Implementation

**start_ui.sh:**
```bash
mesop main.py --port=3000 --reload
```

**start_newsroom.sh with `--with-ui --reload`:**
```bash
if [ -n "$RELOAD_FLAG" ]; then
    UI_RELOAD="--reload"
fi
mesop main.py --port=3000 $UI_RELOAD
```

## Limitations

1. **State is not preserved** - When UI reloads, all in-memory state is lost
   - Stories in `app_state.stories_cache` are cleared
   - Users need to reassign story if reload happens during workflow

2. **Browser refresh required** - Hot reload restarts server, but doesn't auto-refresh browser
   - Must manually refresh browser to see changes

3. **WebSocket connections** - If using WebSockets in future, they'll disconnect on reload

## Best Practices

### Do:
- ✅ Use hot reload during development
- ✅ Test changes incrementally
- ✅ Keep browser dev tools open to see errors
- ✅ Save files individually (not batch saves)

### Don't:
- ❌ Use hot reload in production
- ❌ Rely on state surviving reloads
- ❌ Make changes while story is in progress (data will be lost)

## Disabling Hot Reload

If you need to disable hot reload:

**For UI only:**
Edit `start_ui.sh` and remove `--reload`:
```bash
mesop main.py --port=3000  # No --reload flag
```

**For full stack:**
Start without `--reload` flag:
```bash
./start_newsroom.sh --with-ui  # No --reload
```

## Troubleshooting

### Hot reload not working

**Check if UI is running in reload mode:**
```bash
ps aux | grep mesop
```

Look for `--reload` in the command.

**Check logs for reload events:**
```bash
tail -f logs/UI.log | grep -i reload
```

### UI crashes on reload

**Check for syntax errors:**
```bash
tail -50 logs/UI.log
```

**Verify imports:**
```bash
cd ui
python -c "from pages import home, article"
```

### Changes not appearing

1. **Clear browser cache** - Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
2. **Check file saved** - Verify timestamp changed
3. **Check logs** - Look for reload event in `logs/UI.log`

## See Also

- [UI README](../ui/README.md) - UI documentation
- [UI Integration Plan](ui-integration-plan.md) - Full UI architecture
- [UI MVP Summary](ui-mvp-summary.md) - MVP features
