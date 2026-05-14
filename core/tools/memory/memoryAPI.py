from datetime import datetime
from pathlib import Path
import re


# __file__ is memoryAPI.py which lives at core/tools/memory/memoryAPI.py
# so we go up 3 levels to get to project root, then into core/memory
root_dir = Path(__file__).parent.parent.parent / "memory"

# ─────────────────────────────────────────
# READ TOOLS
# ─────────────────────────────────────────

def read_shortTerm() -> str:
    """Read the full short term memory file."""
    path = root_dir / "shortTerm.md"
    if not path.exists():
        return "shortTerm.md not found."
    return path.read_text()


def read_midTerm() -> str:
    """Read the full mid term memory file."""
    path = root_dir/ "midTerm.md"
    if not path.exists():
        return "midTerm.md not found."
    return path.read_text()


def read_longTerm() -> str:
    """Read the full long term memory file."""
    path = root_dir / "longTerm.md"
    if not path.exists():
        return "longTerm.md not found."
    return path.read_text()


# ─────────────────────────────────────────
# WRITE TOOLS
# ─────────────────────────────────────────

def update_shortTerm(section: str, content: str) -> str:
    """
    Update a specific section in shortTerm.md.
    Replaces everything after the section header until the next header.

    Args:
        section: The ## section header to update, e.g. "Active Goals (This Week)"
        content: The new content to write under that section (plain text, no header)
    """
    path = root_dir / "shortTerm.md"
    if not path.exists():
        return "shortTerm.md not found."

    text = path.read_text()

    # Update Last Updated timestamp
    now = datetime.now()
    text = re.sub(
        r"Last Updated:.*",
        f"Last Updated: {now.strftime('%Y-%m-%d %H:%M')}",
        text
    )

    # Replace the section content
    pattern = rf"(## {re.escape(section)}\n)(.*?)(?=\n## |\Z)"
    replacement = rf"\g<1>{content.strip()}\n"
    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    if new_text == text:
        return f"Section '## {section}' not found in shortTerm.md."

    path.write_text(new_text)
    return f"Updated '## {section}' in shortTerm.md."


def update_midTerm(section: str, content: str) -> str:
    """
    Update a specific section in midTerm.md.

    Args:
        section: The ## section header to update, e.g. "Goals — Next 3–6 Months"
        content: The new content to write under that section
    """
    path = root_dir / "midTerm.md"
    if not path.exists():
        return "midTerm.md not found."

    text = path.read_text()

    now = datetime.now()
    text = re.sub(
        r"Last Updated:.*",
        f"Last Updated: {now.strftime('%Y-%m-%d')}",
        text
    )

    pattern = rf"(## {re.escape(section)}\n)(.*?)(?=\n## |\Z)"
    replacement = rf"\g<1>{content.strip()}\n"
    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    if new_text == text:
        return f"Section '## {section}' not found in midTerm.md."

    path.write_text(new_text)
    return f"Updated '## {section}' in midTerm.md."


def update_longTerm(section: str, content: str, confirm: bool = False) -> str:
    """
    Update a specific section in longTerm.md.
    Requires confirm=True as a safety gate — long term should rarely change.

    Args:
        section: The ## section header to update
        content: The new content to write under that section
        confirm: Must be True to actually write. Safety gate.
    """
    if not confirm:
        return "Long term memory update blocked. Pass confirm=True to proceed. This file rarely changes — are you sure?"

    path = root_dir / "longTerm.md"
    if not path.exists():
        return "longTerm.md not found."

    text = path.read_text()

    now = datetime.now()
    text = re.sub(
        r"Last Updated:.*",
        f"Last Updated: {now.strftime('%Y-%m-%d')}",
        text
    )

    pattern = rf"(## {re.escape(section)}\n)(.*?)(?=\n## |\Z)"
    replacement = rf"\g<1>{content.strip()}\n"
    new_text = re.sub(pattern, replacement, text, flags=re.DOTALL)

    if new_text == text:
        return f"Section '## {section}' not found in longTerm.md."

    path.write_text(new_text)
    return f"Updated '## {section}' in longTerm.md."


# ─────────────────────────────────────────
# BOOT UTILITIES
# ─────────────────────────────────────────

def get_time_delta() -> float:
    """Return hours since shortTerm.md was last updated."""
    path = root_dir/ "shortTerm.md"
    if not path.exists():
        return 999.0

    text = path.read_text()
    for line in text.split("\n"):
        if line.startswith("Last Updated:"):
            raw = line.replace("Last Updated:", "").strip()
            try:
                last = datetime.strptime(raw, "%Y-%m-%d %H:%M")
                delta = datetime.now() - last
                return delta.total_seconds() / 3600  # return hours
            except ValueError:
                return 999.0
    return 999.0


def inject_datetime() -> str:
    """Stamp current date and time into shortTerm.md on boot."""
    path = root_dir / "shortTerm.md"
    if not path.exists():
        return "shortTerm.md not found."

    now = datetime.now()
    text = path.read_text()

    text = re.sub(r"Last Updated:.*", f"Last Updated: {now.strftime('%Y-%m-%d %H:%M')}", text)
    text = re.sub(r"- \*\*Date:\*\*.*", f"- **Date:** {now.strftime('%A, %B %d, %Y')}", text)
    text = re.sub(r"- \*\*Time:\*\*.*", f"- **Time:** {now.strftime('%I:%M %p')}", text)

    path.write_text(text)
    return f"Datetime injected: {now.strftime('%A %B %d %Y, %I:%M %p')}"


def load_all_memory() -> str:
    """Load all three memory files into a single string for system prompt injection. and preferences file"""
    files = ["longTerm.md", "midTerm.md", "shortTerm.md", "preferences.md"]
    sections = []
    for f in files:
        p = root_dir / f
        if p.exists():
            sections.append(p.read_text())
        else:
            raise FileNotFoundError(f" file not found: {p}")
    return "\n\n---\n\n".join(sections)

def count_tokens(text: str) -> int:
    """Rough token estimate — ~4 chars per token."""
    return len(text) // 4

def boot_refresh() -> str:
    """
    Run on every Jarvis boot.
    Injects datetime and decides what else to refresh based on time delta.
    """
    hours = get_time_delta()
    log = []

    log.append(inject_datetime())

    if hours >= 168:  # 7+ days
        log.append("[Jarvis] 7+ days since last session — consider reviewing midTerm.md")
        log.append("[Jarvis] Full STM review recommended")
    elif hours >= 24:  # 1+ days
        log.append("[Jarvis] 1+ days since last session — STM goals may be stale")
    elif hours >= 1:  # same day, been a while
        log.append("[Jarvis] Same-day resume")
    else:
        log.append("[Jarvis] Recent session — datetime updated only")

    return "\n".join(log)