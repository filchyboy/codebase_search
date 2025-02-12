## REPL Mode Implementation

The REPL (Read-Eval-Print Loop) functionality for the code-search-cli application is located in:
	•	It is managed within cli.py, ensuring that after any command (search, exclusions, etc.), control is returned to the REPL.
	•	Command execution is structured so that the REPL remains active instead of exiting after a single command.

**Behavior**
	•	Running code-search launches the interactive REPL.
	•	Any command executed inside the REPL (search, exclusions, etc.) runs normally and then returns control to the REPL.
	•	Users can input search queries directly without prefixing them with search, making it a seamless experience.

**Implementation Details**
	•	The REPL loop is responsible for handling user input, dispatching commands, and maintaining session state.
	•	The primary entry point is inside cli.py, where:
	•	If no command is explicitly provided, the REPL is invoked.
	•	If a command is executed, it runs, and then the REPL resumes.
	•	The help_command.py file includes documentation on how the REPL works and available commands.

### Running Searches from the Command Line

In addition to running searches inside the REPL, users can also search directly from the command line without entering the REPL.

**Basic Search**

To search for a term across the codebase, run:

```bash
code-search search "function_name"
```

This will return results where "function_name" appears in the files.

**Using Regular Expressions**

You can use grep-style regex patterns for more advanced searches:

```bash
code-search search "(?i)error handling"
```

This performs a **case-insensitive** search for "error handling".

**Excluding Directories**

By default, code-search automatically excludes common directories like `.git`, `node_modules`, `venv`, and `__pycache__`. You can override exclusions or add new ones.

To list **current exclusions**:

```bash
code-search exclusions list
```

To add an **exclusion pattern**:

```bash
code-search exclusions add "*.log"
```

**Changing the Search Directory**

If you need to search in a different directory, you can initialize code-search with a new base directory:

```bash
code-search init --base-dir /path/to/your/code
```

This sets the directory that will be used for future searches.