# AIRproject: a reconstructed history

This is a dated timeline of the project, built ~Aug–Oct 2024, before coding agents
existed. It was reconstructed on 2026-07-14 from two documents produced during a
review of Scott's conversation and code archives:

- `airproject-bisect.md` — a bisection of this repository's actual, real (unsquashed)
  git history: what the committed code did at each commit, verified by reading the
  code and, where local drive artifacts existed outside git, by real program output.
- `airproject-history.md` — a reconstruction from Scott's claude.ai and ChatGPT
  conversation archives: what was discussed, drafted, and pasted into chat, including
  code that was never committed.

Every claim below is tagged with its evidence type:

- **[COMMIT]** — directly verifiable from this repository's git history (`git log`,
  `git diff`) or from reading the committed files.
- **[CONVERSATION]** — recovered from a dated chat transcript in Scott's archives; not
  independently verifiable from the repository itself. Quotes are verbatim from the
  source document, with the conversation identifier given.
- **[RUNTIME, non-git]** — from output files that exist on a local drive copy of the
  project directory but were never tracked in git (so they don't show up in the
  history above), showing what actually happened when the code ran.
- **[INDETERMINATE]** — the record does not resolve this question. Stated as open,
  not glossed over.

A recurring theme in this project's history: "was discussed or drafted in chat" and
"was committed to the repository" are not the same claim, and in the central episode
below (September 11–16, 2024) they diverge. Read "ran" and "was committed" as
separate facts throughout.

---

## 1. Founding and the day-two cross-model review (2024-08-21 – 08-23)

- **2024-08-22** — Design and naming. The project's founding design statement lays
  out CRUD-style file tools, one conversation-file per target file, and multi-provider
  intent; the tool is named "airproject" the same day. **[CONVERSATION]**
  (convs `d81b1245` "Collaborative Code Review Tool," `e5955db2` "Kickstarting
  AI-Assisted Software Development.")
- **2024-08-23** — An MVP exists: a `click` CLI, a `.aiproject.json` marker file, a
  `conversations/` directory, CRUD file tools, and a manual tool loop calling
  `claude-3-opus-20240229`. **[CONVERSATION]**
- **2024-08-23, 16:43** — Scott brings that MVP's actual source code, plus a sample
  API transcript, to ChatGPT for independent review — one day after founding.
  Verbatim, his stated reason for not asking Claude to review its own output:
  *"Since you are different from Claude, I wonder if you can analyze the code, and
  sample API interactions, without being influenced in that way."* ChatGPT flags a
  real design gap (no termination guard on the recursive tool loop) and an
  over-verbose system prompt. **[CONVERSATION]** (conv `1277` "Model Meta-Confusion
  Analysis")
- **2024-08-23 08:40:56 -0400** — First commit, `f574864` "Init." Static analysis of
  this commit's `airproject.py` shows OpenAI-shaped tool definitions
  (`{"type": "function", "function": {...}}`) passed to Anthropic's
  `client.messages.create`, checking response fields (`response.content[0].type ==
  'function_call'`) that don't exist in Anthropic's response schema. Never
  functional. **[COMMIT]**

## 2. Rebuild against "current" SDK, and the bug (2024-09-08 – 09-09)

- **2024-09-08 21:50:48 -0400**, commit `83b1434` "Update to current SDK" — the tool
  list is reduced to `tools = [# ... (keep the existing tool definitions)]`, i.e. an
  empty list. With no tools declared, the model can never return a `tool_use` block,
  so the tool-handling code is dead regardless of its own (also present) bugs.
  **[COMMIT]**
- **2024-09-09** — Scott hits and reports a real crash: `AttributeError: 'ToolUseBlock'
  object has no attribute 'text'`. This confirms the Anthropic API was genuinely being
  called and genuinely returning a real `ToolUseBlock` at this point in development —
  a real round trip that crashed on the client side, not a hallucinated or
  never-attempted one. Claude, in-chat, repeatedly proposes OpenAI-shaped fixes
  despite being told to check current SDK docs; one such fix is live-tested against
  the real Anthropic API and rejected: `Bad request: ... 'tools.0.name: Field
  required'`. **[CONVERSATION]** (conv `897adde6` "Troubleshooting AttributeError in
  ToolUseBlock," 2024-09-09 13:46 UTC)

## 3. The correct fix, drafted in conversation and never committed (2024-09-11)

- Scott pastes a real printed object repr from an actual run:
  `ToolUseBlock(id='toolu_01Ep4fG9rEzgYegaiiRgrFGX', input={}, name='list_files',
  type='tool_use')`. With the real shape in hand, the correct fix is written in-chat:
  `function_name = content_block.name` / `arguments = content_block.input`. Per the
  bisect document, this "exists as a full `airproject.py` artifact in this
  conversation" — i.e. more than the two-line pattern quoted here was drafted, though
  only this pattern is reproduced verbatim in the source documents this file draws
  from. That draft still carried two further bugs (`role="tool"` instead of `"user"`;
  `tool_call_id=` instead of `tool_use_id=` in `ToolResultBlockParam`), so even this
  best-found draft would not have completed a full round trip without additional
  fixes. **[CONVERSATION]** (conv `0f6afc41` "Updating code to use ContentBlock .type
  field," 2024-09-11 11:37 UTC)
- **This fix was never committed.** No commit in the repository's real history
  contains `content_block.name` / `content_block.input` in `handle_tool_use`.
  **[COMMIT — absence confirmed by bisecting all three states `airproject.py` ever
  had]**
- Separately, the same day, a different thread asks for a stripped-down "bootstrap"
  script — at that point still explicitly Claude/Anthropic-native (`from anthropic
  import Anthropic`). **[CONVERSATION]** (conv `a6174a37` "Simplified AI-Assisted
  Script for Collaborative Editing")

## 4. What actually got committed instead (2024-09-16)

- **2024-09-16 18:33:06 -0400**, commit `b641f60` "Bootstrap is able to read and
  write target file." Tool definitions are now correctly shaped (`ToolParam` with
  `input_schema`), and the SDK-version check (`content.type == 'tool_use'`) is
  correct. But `handle_tool_use` reverted to the earlier, wrong guess — it checks
  `hasattr(content_block, 'tool_call')` / `hasattr(content_block, 'tool_calls')`,
  neither of which exists on a real `ToolUseBlock` (whose real attributes are `.name`
  and `.input`, exactly as found in conversation five days earlier). Both `hasattr`
  checks always fail, so the function always falls through to `return None` — no tool
  ever executes through this path. Downstream, the follow-up message uses
  `role="tool"` (invalid) and `tool_call_id=` (wrong key), but that code is never
  reached anyway. **[COMMIT — static analysis]**
- **`airproject.py` has been byte-identical since this commit** — confirmed via
  `git diff b641f60 HEAD -- airproject.py` (empty) at the time of this writing.
  Everything below in §7 is packaging/docs, not a functional change to this file.
  **[COMMIT]**
- Runtime consequence, confirmed by real output on a local (non-git) drive copy:
  `conversations/HelloWorld2.txt` shows Claude hallucinating file listings
  ("HelloWorld2.txt," then "hello_world.py.x," "README.md") that don't match the
  real, empty project directory, and a burst of near-identical blank "## Assistant"
  entries seconds apart (07:57:50 through 07:58:00) — the signature of an unbounded
  loop: no tool result is ever appended to the message list, so the `while True` loop
  resubmits unchanged state forever. **[RUNTIME, non-git]**
- The same commit introduces `bs.py`, fully OpenAI-based (`from openai import
  OpenAI`, legacy `ChatCompletion`/`function_call` API) — a different code lineage
  from the Claude-native bootstrap sketch discussed on 2024-09-11 (§3). **[COMMIT]**

## 5. The loop that actually ran: the OpenAI-side bootstrap (2024-09-11 – 09-20)

Roughly three weeks after founding, and the same evening as the fix drafted in §3,
Scott gets his first OpenAI API key and starts a second, deliberately minimal,
self-editing tool from scratch on the OpenAI side.

- **2024-09-11, 12:53–22:33** — Bootstrap conceived and specced; that evening, four
  successive real tracebacks (`APIRemovedInV1`, a `chat_create` `AttributeError`, a
  `.get` on a pydantic object) from the real path
  `/run/media/scottvmcguire/Extreme Pro/mysrc/ToGitHub/airproject/bs.py`, in a pyenv
  virtualenv named "airproject." **[CONVERSATION]** (conv `1216` "OpenAI API Python
  Example")
- **2024-09-12, 12:21:22** — Scott supplies a fix himself rather than waiting on the
  model, verbatim: *"This is how we should convert to json:
  json.dump(message.model_dump(), file)"* — direct evidence of hands-on debugging
  work, not purely relaying to the model. **[CONVERSATION]** (conv `1215` "Fixing
  OpenAI Python Client")
- **2024-09-18, conv `1194`** ("Progress Indicators in Code") — a real functional bug
  is found and diagnosed: asking the agent to "add a comment" replaced the whole
  target file instead of appending. Scott's own diagnosis, verbatim: *"the agent will
  need to send the entirety of the new file to the write function."* Same thread,
  Scott's own progress read, verbatim: *"This is working better."* **[CONVERSATION]**
- **2024-09-20, conv `1185`** ("Code Flow Debugging") — a pasted run log shows the
  tool loading its history (3 entries), readying its functions, and executing up to
  a real API error (`Missing parameter 'name': messages with role 'function' must
  have a 'name'`) — the clearest single piece of "it actually ran" evidence found on
  the OpenAI side. **[CONVERSATION]**
- Independently, on a local (non-git) drive copy: `airproject_history.txt`/`.json`
  and `test_file.txt` show `target.py` — driven by the OpenAI legacy `function_call`
  API, same lineage as `bs.py` — genuinely executing `read_file`/`write_file` against
  itself and evolving its own code across several iterations. **[RUNTIME, non-git]**
- **2024-09-20 15:55:45 -0400**, commit `2005397` "Switch to gtp4. Revert to version
  of APO that ChatGPT knows." — the last commit that substantively touches the
  tool-use code. Every commit after this is README or dependency-pinning work.
  **[COMMIT]**

No message found anywhere in the OpenAI-side record says the tool "fully works" —
the positive signals are the ones quoted above ("This is working better," and the
run log proving real execution up to a real, later-fixed API error), not a clean
end-to-end success statement.

## 6. Later meta-work, and the open Gemini question (2024-09-25 – 10-04)

- **2024-09-25 – 09-26** — A LangChain rewrite (`ChatAnthropic` +
  `OpenAIFunctionsAgent` + `AgentExecutor`); an MVP plan with a `ModelInterface`
  abstract base class and a `ClaudeAdapter`; git integration so `submit` auto-commits
  after each AI turn; and an SDK-documentation-generator project that has the
  Anthropic API itself (`claude-3-sonnet-20240229`, `max_tokens=100000`) read the
  whole current Anthropic Python SDK source and write a reference doc, to counter the
  problem of models being trained on stale SDK versions. **[CONVERSATION]** (convs
  `8cff533b`, `4a04cd8b`, `6438e282`, `b4b3aaa9`)
- **On Gemini, specifically — OPEN, do not treat as resolved.** The one Gemini
  mention found in the swept corpus (2024-09-26) is a failed attempt to ask Gemini's
  *chat interface* to describe the SDK from its own training knowledge — not a script
  calling the Gemini API to read source — and it failed: *"The generated document was
  clearly incomplete as I could verify by looking at the official documentation."*
  The read/write SDK-documentation work that did demonstrably run in this window used
  the Anthropic API (Claude reading its own SDK's source), not Gemini. **Scott has
  disputed this reading (2026-07-14): "I feel reasonably strongly that's not the
  complete SDK -> Gemini history. I'll search."** Pending that search, this question
  is OPEN. **[INDETERMINATE]**
- **2024-10-04** — A downstream continuation: *"I have let an LLM read the code for
  the SDK and attempt to write documentation."* The record does not name which model
  performed this specific run. **[INDETERMINATE]** (conv `a10f2d55`)

## 7. Wind-down (October 2024) and no further plumbing work since

- **2024-10-05 – 10-17** — Scott evaluates purpose-built alternatives in the same
  weeks: GPT Canvas (Oct 5, Oct 11); a direct, dated adoption statement, verbatim,
  Oct 8: *"I plan to use Cursor."*; LangChain studied as a framework (Oct 17), the
  same day as the last airproject-related conversation found in either corpus (Oct
  17, conv `1102` "Handling Multiple Conversation Roles"). **[CONVERSATION]**
- **No explicit "I'm stopping" statement was found anywhere in the swept record.**
  An employment change falls in the same window (September–October 2024), but the
  related conversations were not in the airproject-specific conversation set
  searched for this document — noted here only as plausible timing context, not
  asserted as the cause. **[INDETERMINATE]**
- **2025-09-03**, commit `c4c4c09` "Update README.md." **2026-07-05**, commits
  `0263bdd` (README fixes, run notes) and `ef45975` ("Pin httpx<0.28 (older anthropic
  SDK incompatible with httpx 0.28+)" — a packaging-compatibility pin, not a
  functional fix to the §3–4 bug). **2026-07-07**, commit `1656683` (README
  provenance note). **2026-07-13**, commit `f90e03d` (SECURITY.md, gitleaks
  workflow). None of these touch `airproject.py`'s tool-use code. **[COMMIT]**

## 8. Bottom line

- No committed state of `airproject.py`, across the repository's full, real
  (unsquashed) git history, ever had correct Anthropic tool-use plumbing. **[COMMIT]**
- A correct fix for the core bug was drafted and verified against a real object repr
  in conversation on 2024-09-11, but never made it into a commit; the commit that
  landed five days later reverted to the earlier, wrong attribute-access guess.
  **[CONVERSATION + COMMIT, cross-referenced]**
- The loop that demonstrably read and wrote files against a real target, across
  multiple iterations, driven by real API calls, was the OpenAI-based bootstrap
  (`bs.py` → `target.py`), not the Anthropic/Claude path. **[CONVERSATION +
  RUNTIME, non-git]**
- The project wound down in October 2024, in the same weeks purpose-built AI coding
  tools (Cursor, GPT Canvas) were being evaluated and adopted, and a job transition
  was underway. No single explicit stopping statement was found. **[INDETERMINATE]**

---

*Sourcing note: reconstructed 2026-07-14 from `live/notes/fresh-pass/airproject-bisect.md`
and `live/notes/fresh-pass/airproject-history.md`, produced during a review of Scott's
git, claude.ai, and ChatGPT archives. This document does not independently re-verify
claims beyond what those two source documents state, and does not reproduce full
conversation text — see the original archives (conversation UUIDs cited above) for
anything beyond what's quoted here. The claude.ai-side conversations marked
`[title-only]` in the source history document (identified by date/title but not
opened) are not represented here at all; treat this timeline as complete for what it
covers, not as a guarantee that nothing else exists in the unopened set.*
