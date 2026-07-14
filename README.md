# Air Project

As I started to rely more on LLMs to help with coding, I wanted something better than copying and pasting between chats in a web browser and my text editor.
At around the same time I had started relying heavily on the Projects feature of Claude largely because it made it easy to save artifacts generated in a conversation to project knowledge.
With some manual help, this could emulate a small filesystem in which Claude could edit files (Claude writes a new version, I delete the old one) and this worked for small coding projects.
But it was cumbersome and when I learned about tool use, I thought it would be possible to do better by creating a command line chat tool that would access my filesystem via tools.
At the time I was also jumping back and forth between Claude, ChatGPT, and Gemini, pasting the same queries into each, or getting critiques of one's output by another.
So I thought this tool should also be multi-model.

Some initial attempts, at different times with help of different chat models, kind of worked in a formal way. I could send a message and get a response, maybe get a file read, etc.
But progress was slow and the LLM-written code tended to be buggy or convoluted.

One particular issue was that all of the LLMs had been trained on versions of the SDKs or sometimes APIs which were pretty out of date.
This led to a side project trying to get an LLM to write a good, one-page document of the Anthropic Python SDK from the source code.
This ended up being Gemini (I don't recall the version) because the large context window made it much easier.
The results were not entirely useless, but I found that even sharing that document with the models it was hard to get them to use that knowledge rather than what they were trained on.

I decided to narrow the scope for an MVP.
This would be just Claude, via the Anthropic Python SDK.
We got a simple version working, sufficient to start testing.
While the plumbing worked, it just didn't work as well as Claude in the Claude Projects environment.
This led to me poking around and learning about the implementation of Claude Projects.
I had not known that all of project knowledge was inserted into Claude's context.
(Interestingly, neither did Claude. We found out together via experiments. "I just added XXX to project knowledge, do you see it? Where? ...")
I learned that this was critical to the performance I was getting in the Projects environment.
There, Claude had an ambient awareness of what was in project knowledge.
In my implementation, Claude could read (and write) files if directed to, but didn't naturally go looking for things.
This makes sense in retrospect --- I hadn't given it any knowledge about what was in the files which would let it figure out when they were worth looking at.
There were potentially ways to move forward, such as a search tool or an index that would be automatically kept up to date, but I stopped here.

And now we have Claude Code.

## Running it

`airproject.py` is the Claude MVP (Click CLI, filesystem tools); `bs.py` is
an earlier OpenAI-based bootstrap script. As of the July-2026 rehabilitation
(see Code Archaeology below), `airproject.py` runs against the current
`anthropic` SDK (0.95.x, model claude-haiku-4-5) and the old pinned-SDK /
`httpx<0.28` constraint no longer applies. `bs.py` remains period code
(openai 0.27-era) and is not expected to run today.

---

*Postscript, July 2026.* In retrospect this was an attempt at Claude Code
before Claude Code existed: a command-line chat tool with filesystem access
via tool use. The honest comparison: Claude Code works, and this didn't
quite. But the diagnosis above held up — ambient context was the missing
piece, and giving the model standing awareness of the workspace, rather
than tools it had to think to use, is exactly what the products that
succeeded got right.

One more note, since my later repos carry provenance statements: this one
predates coding agents, and every line here passed through my hands —
drafted in web-chat conversations, hand-applied, and debugged by me
personally. It's the baseline my later delegation experiments are measured
against.

## Code Archaeology

*This section was compiled by Claude agents (July 2026) from the git history
plus recovered 2024 conversation transcripts. Full detail, with per-claim
evidence tags, in [docs/HISTORY.md](docs/HISTORY.md).*

- **2024-08-21** — repo founded: AI pair-programming from scratch,
  deliberately minimal.
- **2024-08-23 (day two)** — the MVP went to a cross-model review ("Since
  you are different from Claude...") — multi-model review from the start.
- **2024-09-08/09** — rebuilt against the then-current SDK; the tool-use bug
  appears. Sept 9: a real crash (`AttributeError: 'ToolUseBlock' object has
  no attribute 'text'`) proves a live round trip was being attempted.
- **2024-09-11** — the correct attribute-access fix was drafted in
  conversation and verified there against a real logged `ToolUseBlock` —
  but never committed.
- **2024-09-16** — the commit that landed instead reverted to an
  OpenAI-shaped `hasattr` guess; no committed state of the Claude path
  worked, from founding until 2026.
- **2024-09-11→20** — what demonstrably did work: the OpenAI bootstrap loop
  (`bs.py` → `target.py`), real read/write round trips against a target
  project.
- **2024-09→10** — the SDK-documentation side quest described above ran
  across Claude, ChatGPT, and a Gemini 1.5 Pro generator whose output
  survives (dated 2024-10-04).
- **2024-10** — wind-down, with dated context rather than a stopping declaration:
  purpose-built tools were arriving and being evaluated ("I plan to use Cursor,"
  Oct 8; GPT Canvas that same week) while a new job's onboarding absorbed the
  time. Later commits are packaging and docs only.
- **2026-07-14** — rehabilitation: the 2024 session draft landed, plus two
  further bug layers that draft didn't cover (one only discoverable against
  the live API), a modern SDK, and a passing live tool round trip. The loop
  closed 22 months after the bug was first diagnosed.
