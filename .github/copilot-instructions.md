## Just Command Usage

Before running any terminal commands, always check the `justfile` first to see if there's an existing command for the task you want to perform. This project uses [just](https://github.com/casey/just) as a command runner for common development tasks.

### Workflow:

1. **Always check the `justfile` first** - Run `just --list` or examine the `justfile` to see available commands
2. **Use existing just commands** when available instead of running raw commands
3. **Add new commands to `justfile`** if you find yourself running common commands that aren't already defined

### Examples of when to add commands to the `justfile`:

- Database operations (migrations, seeding, etc.)
- Testing commands
- Build/deployment processes
- Common development workflows
- Docker container management
- Environment setup tasks

Use `just --list` to see the complete list of available commands.
