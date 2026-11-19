"""Spike 0 test cases. All scenarios are fictional.

Each case:
- id: stable identifier
- group: "call" (should call a tool), "no_call", or "hard" (needs enum filters)
- prompt: user message
- expected_tool: tool name, or None when no tool should be called
- expected_args: argument values that must match exactly (others only need to be schema-valid)
"""

CASES = [
    # --- should call a tool (16: 8 English, 8 Chinese) ---
    {"id": "C01", "group": "call", "prompt": "Parse the alarm log at logs/unit07_alarms.csv and list the events.",
     "expected_tool": "parse_log", "expected_args": {"file_path": "logs/unit07_alarms.csv"}},
    {"id": "C02", "group": "call", "prompt": "幫我解析 logs/pcs_alarm_0412.csv 這份告警紀錄。",
     "expected_tool": "parse_log", "expected_args": {"file_path": "logs/pcs_alarm_0412.csv"}},
    {"id": "C03", "group": "call",
     "prompt": "Anonymize this text before I share it: 'Unit SN 4F7K-22-0091 at 10.2.3.14 tripped at 14:02.'",
     "expected_tool": "anonymize", "expected_args": {}},
    {"id": "C04", "group": "call",
     "prompt": "請先把這段訊息去識別化：「設備序號 AB12-7781，IP 192.168.10.5，於 03:15 發生直流過壓。」",
     "expected_tool": "anonymize", "expected_args": {}},
    {"id": "C05", "group": "call", "prompt": "Summarize the events in log LOG-0007. Which alarm came first?",
     "expected_tool": "summarize_events", "expected_args": {"log_id": "LOG-0007"}},
    {"id": "C06", "group": "call", "prompt": "統計 LOG-0012 裡各告警出現的次數。",
     "expected_tool": "summarize_events", "expected_args": {"log_id": "LOG-0012"}},
    {"id": "C07", "group": "call", "prompt": "Find past cases about DC bus overvoltage during discharge.",
     "expected_tool": "search_cases", "expected_args": {}},
    {"id": "C08", "group": "call", "prompt": "找一下有沒有冷卻風扇故障導致降載的案例。",
     "expected_tool": "search_cases", "expected_args": {}},
    {"id": "C09", "group": "call", "prompt": "Any similar cases where the PCS failed to synchronize with the grid on startup?",
     "expected_tool": "search_cases", "expected_args": {}},
    {"id": "C10", "group": "call", "prompt": "有沒有通訊中斷造成 PCS 停機的相關案例？",
     "expected_tool": "search_cases", "expected_args": {}},
    {"id": "C11", "group": "call", "prompt": "Show me the full details of case CASE-014.",
     "expected_tool": "get_case", "expected_args": {"case_id": "CASE-014"}},
    {"id": "C12", "group": "call", "prompt": "把 CASE-003 的完整內容調出來。",
     "expected_tool": "get_case", "expected_args": {"case_id": "CASE-003"}},
    {"id": "C13", "group": "call", "prompt": "Open case CASE-027.",
     "expected_tool": "get_case", "expected_args": {"case_id": "CASE-027"}},
    {"id": "C14", "group": "call", "prompt": "讀取 data/export_2026-05.csv 並列出事件。",
     "expected_tool": "parse_log", "expected_args": {"file_path": "data/export_2026-05.csv"}},
    {"id": "C15", "group": "call", "prompt": "Give me a timeline of LOG-0031.",
     "expected_tool": "summarize_events", "expected_args": {"log_id": "LOG-0031"}},
    {"id": "C16", "group": "call", "prompt": "查詢 IGBT 模組過溫的歷史案例。",
     "expected_tool": "search_cases", "expected_args": {}},
    # --- should NOT call a tool (4) ---
    {"id": "N01", "group": "no_call", "prompt": "What does PCS stand for in a battery energy storage system?",
     "expected_tool": None, "expected_args": {}},
    {"id": "N02", "group": "no_call", "prompt": "什麼是 IGBT？用一句話解釋。",
     "expected_tool": None, "expected_args": {}},
    {"id": "N03", "group": "no_call", "prompt": "Thanks, that's all for now.",
     "expected_tool": None, "expected_args": {}},
    {"id": "N04", "group": "no_call", "prompt": "直流側和交流側的差別是什麼？",
     "expected_tool": None, "expected_args": {}},
    # --- hard: enum filters must be filled correctly (4) ---
    {"id": "H01", "group": "hard",
     "prompt": "Search cases only for the cooling system while the unit was charging: fan speed alarm.",
     "expected_tool": "search_cases", "expected_args": {"component": "cooling", "operating_mode": "charging"}},
    {"id": "H02", "group": "hard", "prompt": "只找放電模式下、功率模組相關的案例：過溫跳機。",
     "expected_tool": "search_cases", "expected_args": {"component": "power_module", "operating_mode": "discharging"}},
    {"id": "H03", "group": "hard", "prompt": "Find BMS interface cases during startup/shutdown, top 3 only.",
     "expected_tool": "search_cases",
     "expected_args": {"component": "bms_interface", "operating_mode": "startup_shutdown", "k": 3}},
    {"id": "H04", "group": "hard", "prompt": "在待機狀態下，輔助電源相關的故障案例有哪些？",
     "expected_tool": "search_cases", "expected_args": {"component": "auxiliary_power", "operating_mode": "standby"}},
]
