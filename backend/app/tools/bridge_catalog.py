"""Local Agent Bridge tools — executed on the user's paired machine."""

BRIDGE_TOOL_NAMES = (
    "bridge.list_dir",
    "bridge.read_file",
    "bridge.write_file",
    "bridge.run_command",
)

BRIDGE_TOOL_DEFINITIONS: dict[str, dict] = {
    "bridge.list_dir": {
        "description": "List files and folders on the user's connected local machine (read-only).",
        "schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path relative to allowed project roots, or absolute within roots.",
                },
            },
            "required": ["path"],
        },
    },
    "bridge.read_file": {
        "description": "Read a text file from the user's connected local machine (max 512KB).",
        "schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path within allowed roots."},
            },
            "required": ["path"],
        },
    },
    "bridge.write_file": {
        "description": (
            "Write or overwrite a text file on the user's machine. "
            "Requires user consent on the Bridge app. Device must have write capability."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path within allowed roots."},
                "content": {"type": "string", "description": "Full file content to write."},
            },
            "required": ["path", "content"],
        },
    },
    "bridge.run_command": {
        "description": (
            "Run a shell command on the user's machine inside an allowed directory. "
            "Requires explicit user consent in the Bridge terminal. 60s timeout."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute."},
                "cwd": {
                    "type": "string",
                    "description": "Working directory within allowed roots (default: first root).",
                },
            },
            "required": ["command"],
        },
    },
}