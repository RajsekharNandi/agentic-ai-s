# Email + Calendar Agent

An autonomous agent that reasons about your request, then **actually sends a real
email and/or creates a real Google Calendar event** — no confirmation step, no
simulation. Built for a live classroom demo of tool calling + autonomy.

## How it works

```
You type a request
      │
      ▼
Groq LLM (the "Brain") reads it + decides which tool(s) are needed
      │
      ▼
Python executes the real tool(s):
   - send_email()            → Gmail API
   - create_calendar_event() → Google Calendar API
      │
      ▼
Result goes back to the LLM → it gives you a plain-English confirmation
```

Everything is kept in a running conversation history, so you can say "actually
push it to 4pm instead" in the next message and it will remember what "it" refers to.

---

## Step 1 — Get a Groq API key (2 minutes)

1. Go to https://console.groq.com/keys
2. Sign up / log in, click **Create API Key**, copy it.

## Step 2 — Enable Gmail + Calendar APIs on Google Cloud (10 minutes, one-time)

1. Go to https://console.cloud.google.com/ and create a new project (any name,
   e.g. "email-calendar-agent").
2. In the search bar, search **Gmail API** → click it → **Enable**.
3. Search **Google Calendar API** → click it → **Enable**.
4. Go to **APIs & Services → OAuth consent screen**:
   - User type: **External** (unless you have a Google Workspace org).
   - Fill in app name (e.g. "Classroom Agent"), your email for support/developer contact.
   - Under Data Access, On the **Scopes** step, add:
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/calendar`
   - On the **Test users** step, add your own Gmail address. (While the app is
     in "Testing" mode, only accounts you list here can use it — that's fine
     for a demo.)

5. Way 1:
  Click the "Clients" item in the left sidebar (or click the "Create OAuth client" button visible on your screen).
    Application type → select "Desktop app" (this matters — the code expects a Desktop app client).
    Give it any name, e.g. "Classroom Agent."
    Click Create, then Download JSON.
    Rename that downloaded file to exactly `credentials.json` and put it in the same folder as agent.py.

    OR 
  Way 2:
  Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**:
   - Application type: **Desktop app**
   - Name it anything, click **Create**.
   - Click **Download JSON**.
  Rename the downloaded file to `credentials.json` and place it in this
   project folder (same folder as `agent.py`).

> This file identifies your app to Google — keep it out of any public repo
> (it's already excluded via `.gitignore` if you set one up).

## Step 3 — Install dependencies

```bash
cd email-calendar-agent
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4 — Add your Groq key

Copy `.env.example` to `.env` and paste in your key:

```bash
cp .env.example .env
```

```
GROQ_API_KEY=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
```

## Step 5 — Run it

```bash
python agent.py
```

**First run only:** a browser window will pop up asking you to log in to Google
and approve the app (since it's in "Testing" mode, you'll see an "unverified
app" warning — click **Advanced → Go to [app name] (unsafe)**, this is normal
for personal/dev OAuth apps). After you approve, a `token.pickle` file is
created and you won't be asked again.

## Try it

```
You: Send an email to john@example.com telling him the workshop is confirmed for Friday
You: Set up a call with priya@example.com tomorrow at 3pm for 30 minutes and let her know
You: Book "Team sync" on my calendar next Monday 10-10:30am
```

The second example is the good demo line for class — it triggers **both**
tools in a single turn (email + calendar), which is exactly the "call multiple
tools when the task needs it" behaviour worth pointing out live.

## Safety notes for the demo

- This agent acts **without asking for confirmation**, by design (per your
  spec). Test it on your own email/calendar first before demoing with real
  student data.
- `sendUpdates="all"` in `create_calendar_event` means any attendees you list
  get a real calendar invite email automatically — good to mention out loud
  in class so it doesn't surprise anyone.
- The OAuth scopes are deliberately narrow: `gmail.send` (cannot read your
  inbox) and `calendar` (can manage events, not other Google data).

## Extending it (good "next step" ideas for students)

- Add a `search_free_slots` tool that checks the calendar before booking, so
  it avoids double-booking — nice segue into "why tools sometimes need to be
  read-only, not just write-only."
- Add a `CONFIRM_BEFORE_SEND` toggle in `.env` to compare autonomous vs
  human-in-the-loop behavior side by side — ties back to the Levels of
  Autonomy slide.
