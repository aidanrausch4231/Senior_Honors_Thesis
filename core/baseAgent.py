import anthropic
from core.models import Model
from core.tools.google.gCalendar_tools import gCalendar_TOOLS, TOOL_MAP
from core.tools.google import gCalendarAPI
from core.tools.memory import memoryAPI

class Agent:
    def __init__(self, api: Model, taskPrompt: str):
        self.api = api
        self.taskPrompt = taskPrompt
        self.history = []
        self.maxHistory = 40
        self.tools = None
        self.tool_map = None

    def chat(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})

        #check
        if len(self.history) >= self.maxHistory:
            self. _summarize_and_trim()

        while True:
            print(f"[Debug] Calling Claude with {len(self.history)} messages in history")
            response = self.api.call(
            self.history,
            system=self.taskPrompt,
            tools=getattr(self, 'tools', gCalendar_TOOLS)
        )
            print(f"[Debug] stop_reason: {response.stop_reason}")
            print(f"[Debug] content blocks: {[b.type for b in response.content]}")

        # Tool call from Claude
            if response.stop_reason == "tool_use":
                self.history.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        print(f"[Debug] Tool call: {block.name}({block.input})")
                        try:
                            fn = self.tool_map[block.name]
                            result = fn(**block.input)
                            print(f"[Debug] Tool result: {result}")
                        except Exception as e:
                            print(f"[Debug] Tool ERROR: {e}")
                            result = f"Error: {e}"
                        tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

                self.history.append({"role": "user", "content": tool_results})

            # Final text response
            else:
                # Check if there are still tool calls hiding in an end_turn response
                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                if tool_blocks:
                    self.history.append({"role": "assistant", "content": response.content})
                    tool_results = []
                    for block in tool_blocks:
                        print(f"[Debug] Tool call: {block.name}({block.input})")
                        try:
                            fn = self.tool_map[block.name]
                            result = fn(**block.input)
                            print(f"[Debug] Tool result: {result}")
                        except Exception as e:
                            print(f"[Debug] Tool ERROR: {e}")
                            result = f"Error: {e}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result)
                        })
                    self.history.append({"role": "user", "content": tool_results})
                    continue  # loop back, let Claude respond to the results

                # Actually just text — return it
                text_block = next((b.text for b in response.content if hasattr(b, "text")), None)
                reply = text_block or "Done."
                self.history.append({"role": "assistant", "content": reply})
                print(f"[Jarvis] {reply}")
                return reply
    def reset(self):
            self.history = []
    async def _summarize_and_trim(self):
        """When history hits X, summarize oldest 10 into STM, keep newest 10."""
        if len(self.history) < self.maxHistory:
            return

        oldest = self.history[:self.maxHistory]   # summarize these
        newest = self.history[10:]   # keep these

        response = self.api.call(
            messages=oldest,
            system="Summarize the key facts, decisions, and action items from this conversation as concise bullet points. Be brief."
        )

        summary = response.content[0].text
        memoryAPI.update_short_term("Recent Context", summary)

        self.history = newest  # trim to newest 10
        print("[Jarvis] History summarized and trimmed")
