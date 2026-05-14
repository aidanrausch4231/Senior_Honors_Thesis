import os
from dotenv import load_dotenv
from core.models import Claude
from core.baseAgent import Agent
from core.bot import TelegramBot, GengiBot
from core.tools.google.gCalendarAPI import get_service, authorize, list_events
from core.organizer import Organizer

load_dotenv()

claude = Claude(api_key=os.getenv("ANTHROPIC_API_KEY"))
organizer = Organizer(api=claude)

GengiBot(os.getenv("TELEGRAM_TOKEN"), organizer).run()
authorize("personal")
