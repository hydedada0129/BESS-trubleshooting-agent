"""Tool schemas offered to the model in Spike 0.

Draft signatures of the five v1 tools (SPEC section 6), in Ollama's
function-calling format. Enum values follow the draft taxonomy (D-17).
"""

COMPONENTS = [
    "dc_side",
    "power_module",
    "ac_grid",
    "cooling",
    "auxiliary_power",
    "communication",
    "bms_interface",
]

OPERATING_MODES = ["charging", "discharging", "standby", "startup_shutdown"]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "parse_log",
            "description": "Parse an alarm log CSV file into a structured event sequence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the alarm log CSV file."},
                },
                "required": ["file_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "anonymize",
            "description": "Remove serial numbers, IPs, MACs, emails and sensitive names from text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to anonymize."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_events",
            "description": "Summarize a parsed log: alarm frequency, first event, and timeline.",
            "parameters": {
                "type": "object",
                "properties": {
                    "log_id": {"type": "string", "description": "ID of a parsed log, e.g. LOG-0007."},
                    "focus": {
                        "type": "string",
                        "enum": ["frequency", "first_event", "timeline"],
                        "description": "Optional aspect to focus on.",
                    },
                },
                "required": ["log_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_cases",
            "description": "Search past troubleshooting cases, optionally filtered by component and operating mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query describing the fault."},
                    "component": {"type": "string", "enum": COMPONENTS},
                    "operating_mode": {"type": "string", "enum": OPERATING_MODES},
                    "k": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Number of results."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_case",
            "description": "Fetch a full troubleshooting case by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "case_id": {
                        "type": "string",
                        "pattern": "^CASE-[0-9]{3}$",
                        "description": "Case ID, e.g. CASE-014.",
                    },
                },
                "required": ["case_id"],
            },
        },
    },
]

SCHEMAS = {t["function"]["name"]: t["function"]["parameters"] for t in TOOLS}
