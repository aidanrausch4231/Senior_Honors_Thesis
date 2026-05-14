# core/organizer.py
from core.baseAgent import Agent
from core.models import Model
from core.tools.google.gCalendar_tools import gCalendar_TOOLS, TOOL_MAP as GCAL_TOOL_MAP
from core.tools.memory.memory_tools import MEMORY_TOOLS, MEMORY_TOOL_MAP
from core.tools.memory import memoryAPI
import json
import threading
import time

ALL_TOOLS = gCalendar_TOOLS + MEMORY_TOOLS
ALL_TOOL_MAP = {**GCAL_TOOL_MAP, **MEMORY_TOOL_MAP}

BASE_PROMPT = """You are Jarvis, Aidan's personal AI assistant.
You have full context about who Aidan is, his current goals, and his projects via the memory files above.
You have access to his Google Calendar and memory tools.

Guidelines:
- Use memory context to personalize every response
- When Aidan completes a goal or starts something new, update shortTerm.md automatically
- When a project ships or major goal is hit, suggest updating midTerm.md
- Never update longTerm.md without explicit confirmation from Aidan
- Keep responses direct and concise — Aidan moves fast
Most important:
    when submitting and organizing
"""


class Organizer(Agent):
    def __init__(self, api: Model):
        super().__init__(api, taskPrompt="")  # base sets up history, api
        self.tools = ALL_TOOLS
        self.tool_map = ALL_TOOL_MAP
        self.taskPrompt = self._load_session()
        self._start_staleness_checker()  # Start background maintenance

    # ─────────────────────────────────────────
    # BOOT
    # ─────────────────────────────────────────

    def _load_session(self) -> str:
        """
        Runs on every boot.
        - Injects current datetime into shortTerm.md
        - Checks staleness of STM and MTM
        - Builds and returns the full system prompt
        """
        print("[Jarvis] Booting...")

        memoryAPI.inject_datetime()
        hours = memoryAPI.get_time_delta()
        days = hours / 24


        print(f"[Jarvis] Last session: {hours:.1f} hours ago")

        self._check_stm_staleness(days)
        self._check_mtm_staleness(days)

        print("[Jarvis] Memory loaded")
        return self._build_system_prompt()

    # ─────────────────────────────────────────
    # STALENESS CHECKS
    # ─────────────────────────────────────────

    def _check_stm_staleness(self, days: float):
        """
        If STM is 7+ days old, ask Claude to review and update Active Goals.
        Auto-updates because STM is low stakes.
        """
        if days < 7:
            return

        print(f"[Jarvis] STM is {int(days)} days old — reviewing goals...")

        stm = memoryAPI.read_short_term()
        response = self.api.call(
            messages=[{"role": "user", "content":
                f"It has been {int(days)} days since short term memory was last updated.\n\n"
                f"Current STM:\n{stm}\n\n"
                f"Which goals are likely stale or completed? "
                f"Return ONLY the updated content for the "
                f"'Active Goals (This Week)' section. "
                f"No header, no preamble, just the bullet points."
            }],
            system="You are Jarvis's memory manager. Be concise. Return only updated content."
        )

        updated = response.content[0].text
        memoryAPI.update_short_term("Active Goals (This Week)", updated)
        print("[Jarvis] STM goals refreshed")

    def _check_mtm_staleness(self, days: float):
        """
        If MTM is 30+ days old, notify Aidan.
        Does NOT auto-update — MTM is higher stakes, Aidan drives this.
        """
        if days < 30:
            return

        print(f"[Jarvis] MTM is {int(days)} days old — mid term goals may need a review")
        print("[Jarvis] Tell me what's changed and I'll update midTerm.md")

    def _start_staleness_checker(self, interval_hours: int = 1):
        """
        Start a background thread to check memory staleness periodically.
        Runs every `interval_hours` (default: 1 hour).
        """
        def check_periodically():
            while True:
                time.sleep(interval_hours * 3600)
                try:
                    hours = memoryAPI.get_time_delta()
                    days = hours / 24
                    self._check_stm_staleness(days)
                    self._check_mtm_staleness(days)
                except Exception as e:
                    print(f"[Jarvis] Error in staleness check: {e}")
        
        thread = threading.Thread(target=check_periodically, daemon=True)
        thread.start()
        print(f"[Jarvis] Background staleness checker started (interval: {interval_hours}h)")

    # ─────────────────────────────────────────
    # SYSTEM PROMPT
    # ─────────────────────────────────────────

    def _build_system_prompt(self) -> str:
        """
        Assembles the full system prompt:
        longTerm + midTerm + shortTerm + base personality
        """
        from datetime import datetime
        now = datetime.now().strftime("%A, %B %d %Y, %I:%M %p")
        memoryPrompt = memoryAPI.load_all_memory()
        toolsPrompt = json.dumps(ALL_TOOLS)
        total = memoryPrompt + toolsPrompt + BASE_PROMPT

        ##token checker:
        print(f"[Jarvis] System memoryPrompt: ~{memoryAPI.count_tokens(memoryPrompt)} tokens")
        print(f"[Jarvis] System toolsPrompt: ~{memoryAPI.count_tokens(toolsPrompt)} tokens")
        print(f"[Jarvis] System basePrompt: ~{memoryAPI.count_tokens(BASE_PROMPT)} tokens")
        print(f"[Jarvis] System: ~{memoryAPI.count_tokens(total)} tokens")

        return (
            f"Current datetime: {now}\n\n"
            f"{memoryPrompt}\n\n"
            f"---\n\n"
            f"{BASE_PROMPT}"
        )

    # ─────────────────────────────────────────
    # HISTORY MANAGEMENT
    # ─────────────────────────────────────────

    def _summarize_and_trim(self):
        """
        When history hits 20 messages:
        - Summarize oldest 10 into shortTerm.md Recent Context
        - Keep newest 10 for live conversation continuity
        """
        print("[Jarvis] History limit reached — summarizing...")

        oldest = self.history[:10]
        newest = self.history[10:]

        response = self.api.call(
            messages=oldest,
            system=(
                "Summarize the key facts, decisions, and action items "
                "from this conversation as concise bullet points. Be brief."
            )
        )

        summary = response.content[0].text
        memoryAPI.update_short_term("Recent Context", summary)

        self.history = newest
        print("[Jarvis] History summarized and trimmed to 10 messages")

    # ─────────────────────────────────────────
    # SESSION END
    # ─────────────────────────────────────────

    def end_session(self):
        """
        Call when Jarvis shuts down or conversation ends.
        Summarizes remaining history into shortTerm.md, then wipes.
        """
        if not self.history:
            print("[Jarvis] No history to summarize")
            return

        print("[Jarvis] Ending session — summarizing to memory...")

        response = self.api.call(
            messages=self.history,
            system=(
                "Summarize the key facts, decisions, and action items "
                "from this conversation as concise bullet points. Be brief."
            )
        )

        summary = response.content[0].text
        memoryAPI.update_short_term("Recent Context", summary)

        self.history = []
        print("[Jarvis] Session saved to shortTerm.md — history cleared")

    # ─────────────────────────────────────────
    # CHAT OVERRIDE
    # ─────────────────────────────────────────

    def chat(self, prompt: str) -> str:
        """
        Extends Agent.chat() with history summarization check.
        Summarizes and trims if history hits 20 messages.
        """

        return super().chat(prompt)