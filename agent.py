"""
agent.py
The "Brain" of the agent. Uses Groq's LLM API with function/tool calling.

Flow:- Model -> Tools -> Memory loop:
  1. User types a request in plain English.
  2. The model decides which tool(s) it needs (send_email, create_calendar_event, both, or none).
  3. Python actually executes the real tool(s) -- no confirmation step, fully autonomous.
  4. The tool result is fed back to the model, which gives a final natural-language answer.
  5. Everything is kept in `history`, so the agent remembers context across turns.
"""

import os
import json
from datetime import datetime

from dotenv import load_dotenv
from groq import Groq

from tools import send_email, create_calendar_event

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Tool schemas -- this is how the model "knows" these Python functions exist

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send a real email via Gmail on behalf of the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Full email body text"},
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create a real event on the user's Google Calendar and optionally invite attendees.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Event title"},
                    "start_datetime": {
                        "type": "string",
                        "description": "Start time in ISO 8601 format, e.g. 2026-08-06T15:00:00",
                    },
                    "end_datetime": {
                        "type": "string",
                        "description": "End time in ISO 8601 format",
                    },
                    "attendees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of attendee email addresses",
                    },
                    "description": {
                        "type": "string",
                        "description": "Event description/notes",
                    },
                },
                "required": ["summary", "start_datetime", "end_datetime"],
            },
        },
    },
]

TOOL_MAP = {
    "send_email": send_email,
    "create_calendar_event": create_calendar_event,
}


def build_system_prompt() -> str:
    now = datetime.now()
    return f"""You are an autonomous Email + Calendar Assistant.

Current date and time: {now.strftime('%A, %Y-%m-%d %H:%M')} (Asia/Kolkata)

Rules:
- You are authorized to act on your own. Once you have enough information, actually
  call the tools -- do NOT ask "should I go ahead?" or "shall I send this?".
- If the user's request implies both emailing someone AND scheduling something
  (e.g. "set up a meeting with X and let them know"), call BOTH tools in the same turn.
- Resolve relative dates/times ("tomorrow", "next Monday 3pm") into exact ISO 8601
  datetimes yourself, using the current date/time given above.
- Only ask a clarifying question if a truly required detail is missing, such as no
  recipient email address at all, or no date/time given for an event.
- After tools run, tell the user clearly and specifically what was actually done
  (e.g. "Sent the email to X and booked the call for 3pm Thursday") -- don't just
  repeat their request back to them.
"""


def run_agent():
    history = [{"role": "system", "content": build_system_prompt()}]
    print("Email + Calendar Agent -- type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        if not user_input:
            continue

        # Refresh "current time" every turn so relative dates stay accurate
        history[0] = {"role": "system", "content": build_system_prompt()}
        history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model=MODEL,
            messages=history,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        # Loop lets the model chain multiple tool calls (e.g. email AND event)
        while msg.tool_calls:
            history.append(msg)

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                print(f"\n[tool call] {tool_name}({tool_args})")

                if tool_name in TOOL_MAP:
                    result = TOOL_MAP[tool_name](**tool_args)
                else:
                    result = {"status": "error", "message": f"Unknown tool: {tool_name}"}

                print(f"[result] {result}\n")

                history.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

            response = client.chat.completions.create(
                model=MODEL,
                messages=history,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )
            msg = response.choices[0].message

        history.append({"role": "assistant", "content": msg.content})
        print(f"Agent: {msg.content}\n")


if __name__ == "__main__":
    run_agent()
