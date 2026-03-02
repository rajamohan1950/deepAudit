"""Maps phases to categories and provides metadata."""

PHASE_DEFINITIONS: dict[int, dict] = {
    1: {
        "name": "Security & Access Control",
        "part": "A",
        "categories": [1, 2, 3, 4, 5],
        "target_signals": 120,
        "prompt_file": "phase_01.yaml",
    },
    2: {
        "name": "Memory, CPU & Network Performance",
        "part": "B",
        "categories": [6, 7, 8],
        "target_signals": 65,
        "prompt_file": "phase_02.yaml",
    },
    3: {
        "name": "Database, Cache, OS & Shutdown",
        "part": "B",
        "categories": [9, 10, 11, 12],
        "target_signals": 70,
        "prompt_file": "phase_03.yaml",
    },
    4: {
        "name": "SPOF, Fault Tolerance & Concurrency",
        "part": "C",
        "categories": [13, 14, 15],
        "target_signals": 70,
        "prompt_file": "phase_04.yaml",
    },
    5: {
        "name": "Data Integrity, Distributed & Queues",
        "part": "C",
        "categories": [16, 17, 18],
        "target_signals": 50,
        "prompt_file": "phase_05.yaml",
    },
    6: {
        "name": "Infrastructure, Capacity, Deploy & Supply Chain",
        "part": "D",
        "categories": [19, 20, 21, 22],
        "target_signals": 80,
        "prompt_file": "phase_06.yaml",
    },
    7: {
        "name": "AI/ML Risks & Operations",
        "part": "E",
        "categories": [23, 24],
        "target_signals": 40,
        "prompt_file": "phase_07.yaml",
    },
    8: {
        "name": "Observability Stack",
        "part": "F",
        "categories": [25, 26, 27, 28],
        "target_signals": 65,
        "prompt_file": "phase_08.yaml",
    },
    9: {
        "name": "Quality, Code, API, UX, Cost & Tenancy",
        "part": "G",
        "categories": [29, 30, 31, 32, 33, 34],
        "target_signals": 100,
        "prompt_file": "phase_09.yaml",
    },
    10: {
        "name": "Compliance, DR, i18n, State, Compat & Org",
        "part": "H",
        "categories": [35, 36, 37, 38, 39, 40],
        "target_signals": 75,
        "prompt_file": "phase_10.yaml",
    },
}


def get_phase(phase_number: int) -> dict:
    return PHASE_DEFINITIONS.get(phase_number, {})


def get_all_phases() -> dict[int, dict]:
    return PHASE_DEFINITIONS


def categories_for_phase(phase_number: int) -> list[int]:
    return PHASE_DEFINITIONS.get(phase_number, {}).get("categories", [])
