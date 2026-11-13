"""Writing rules for every published prose file, checked by tests/test_style.py.

Banned: the em dash and a list of words and phrases that language models overuse (Wikipedia,
"Signs of AI writing"; Kobak et al. 2024/2025 on excess vocabulary). Matching is case-insensitive
and on whole words, so "underscore" also catches "underscores".
"""

EM_DASH = "—"

BANNED = [
    "delve", "delves", "delving", "crucial", "pivotal", "showcase", "showcases", "showcasing", "intricate",
    "robust", "seamless", "seamlessly", "leverage", "leverages", "leveraging", "comprehensive", "notably",
    "underscore", "underscores", "underscoring", "landscape", "realm", "tapestry", "testament", "nuanced",
    "multifaceted", "holistic", "streamline", "streamlines", "empower", "empowers", "harness", "harnesses",
    "unlock", "unlocks", "navigate", "navigates", "navigating",
    "it's important to note", "it is important to note", "it's worth noting", "it is worth noting",
    "in conclusion", "in summary", "let's dive in", "game-changer", "game changer", "in today's",
    "plays a key role",
]

# Exact strings exempt from the em-dash rule: third-party attribution required verbatim.
ALLOWLIST = [
    "Source: Open Dev Data by Electric Capital — https://github.com/electric-capital/open-dev-data",
]

# THESIS.md keeps the pre-registered claims byte-for-byte as committed in 333ea0c, between these markers.
VERBATIM_START = "<!-- pre-registration: start (verbatim from 333ea0c; not restyled) -->"
VERBATIM_END = "<!-- pre-registration: end -->"
