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
- **[SCOTT-SEARCH-VERIFIED]** — found in Scott's own 2026-07 search of his drives and
  Google Drive backups (Codex-assisted) and relayed into this document. The cited
  artifacts live in private storage, not in this repository: internally consistent
  evidence, but not publicly reproducible from the repo alone.

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
- **`airproject.py` was byte-identical from this commit until the 2026-07-14
  rehabilitation (§9)** — confirmed via `git diff b641f60 -- airproject.py` (empty)
  against the pre-rehabilitation tree. Everything below in §7 is packaging/docs, not a
  functional change to this file. **[COMMIT]**
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

## 6. Later meta-work, and the Gemini question (RESOLVED 2026-07-14) (2024-09-25 – 10-04)

- **2024-09-25 – 09-26** — A LangChain rewrite (`ChatAnthropic` +
  `OpenAIFunctionsAgent` + `AgentExecutor`); an MVP plan with a `ModelInterface`
  abstract base class and a `ClaudeAdapter`; git integration so `submit` auto-commits
  after each AI turn; and an SDK-documentation-generator project that has the
  Anthropic API itself (`claude-3-sonnet-20240229`, `max_tokens=100000`) read the
  whole current Anthropic Python SDK source and write a reference doc, to counter the
  problem of models being trained on stale SDK versions. **[CONVERSATION]** (convs
  `8cff533b`, `4a04cd8b`, `6438e282`, `b4b3aaa9`)
- **On Gemini, specifically — RESOLVED. [SCOTT-SEARCH-VERIFIED, 2026-07-14]**
  The corpus-only pass (claude.ai + ChatGPT transcripts) had found only one Gemini
  mention (2024-09-26, a failed attempt to ask Gemini's *chat interface* to describe
  the SDK from its own training knowledge) and marked the SDK→Gemini question OPEN
  after Scott disputed that reading: *"I feel reasonably strongly that's not the
  complete SDK -> Gemini history. I'll search."* Scott's follow-up search, run via
  Codex against his Google Drive (2026-07-14), confirmed his recollection: a Gemini
  1.5 Pro documentation-generator script existed — it imports `google.generativeai`,
  targets model `gemini-1.5-pro`, recursively gathers a project's `.py` files, and
  writes them out as `project_documentation.md`. A generated artifact from that
  script survives in Drive: a ~32KB / 730-line `project_documentation.md`, dated
  2024-10-04, in the folder "mysrc 2/anthropic-sdk-python" — i.e. Gemini reading the
  Anthropic Python SDK's own source, exactly the stale-training-data countermeasure
  described elsewhere in this history, just on the Gemini side rather than the
  Anthropic-API side. Minutes after that file's timestamp, Scott told Claude, verbatim:
  *"I have let an LLM read the code for the SDK and attempt to write documentation."*
  (conv `a10f2d55`, see below) — which this search now identifies as almost certainly
  referring to this Gemini run, not an unnamed Anthropic-API run. Related attempts
  found in the same search, for completeness: a Claude-driven pass on Sept 8–9
  (`tree.txt` + `consolidated.txt`, a directory-tree-plus-concatenated-source
  approach, not a project_documentation.md generator); a Sept 9 manual upload of the
  SDK to ChatGPT (see §4c's `1207`/`1220`); and a Sept 26 proposed
  Claude-3.5-Sonnet-API-driven script that was discussed but not the artifact that
  actually produced the surviving Oct 4 documentation. **[CONVERSATION +
  SCOTT-SEARCH-VERIFIED]**
- **2024-10-04** — A downstream continuation: *"I have let an LLM read the code for
  the SDK and attempt to write documentation."* Per the 2026-07-14 Drive search above,
  this almost certainly refers to the Gemini 1.5 Pro run, not an unnamed Anthropic-API
  run. **[SCOTT-SEARCH-VERIFIED]** (conv `a10f2d55`)

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

- No committed state of `airproject.py`, from the repository's founding through the
  2026-07-14 rehabilitation (§9), ever had correct Anthropic tool-use plumbing.
  **[COMMIT]**
- A correct fix for the core bug was drafted and verified against a real object repr
  in conversation on 2024-09-11, but did not make it into a commit until the §9
  rehabilitation 22 months later; the commit that landed five days after the draft
  reverted to the earlier, wrong attribute-access guess.
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
git, claude.ai, and ChatGPT archives. §10–11 additionally draw on
`live/notes/fresh-pass/airproject-codex-m4-report.md` (the verbatim Codex M4 report,
saved 2026-07-14 evening after it was found to exist only as a synthesis here, not as
its own artifact). This document does not independently re-verify claims beyond what
those source documents state, and does not reproduce full conversation text — see the
original archives (conversation UUIDs cited above) for anything beyond what's quoted
here. The claude.ai-side conversations marked `[title-only]` in the source history
document (identified by date/title but not opened) are not represented here at all;
treat this timeline as complete for what it covers, not as a guarantee that nothing
else exists in the unopened set.*

---

## 9. Postscript — 2026-07-14: the fix lands

Twenty-two months after the bug was found, correctly diagnosed, and then lost, the
Anthropic-side tool-use plumbing in `airproject.py` was fixed and verified against
the live API. Honest attribution, split by what's old and what's new:

- **The core attribute-access fix comes from the uncommitted 2024-09-11 session
  draft, landed today.** Authorship, precisely: Scott supplied the decisive runtime
  evidence (the pasted `ToolUseBlock` repr) and drove the debugging; Claude authored
  the corrected file in that session. `handle_tool_use` now reads
  `function_name = content_block.name` / `arguments = content_block.input` — exactly
  the fix drafted in conversation `0f6afc41` on 2024-09-11 (see §3) and verified there
  against a real logged `ToolUseBlock` repr, but never committed. That draft is landed essentially
  verbatim: the `hasattr(content_block, 'tool_call'/'tool_calls')` guess that had
  been sitting in `handle_tool_use` since the `b641f60` commit (§4) is gone, replaced
  by the two-line fix Scott and Claude found together in 2024. The recovered draft's
  simplified tool-call-ID extraction (`tool_call.id` read straight off the
  `ToolUseBlock`, no more `hasattr` ternary chain) also landed, unchanged in spirit.
- **Everything else is new, 2026 work**, made necessary by 22 months of Anthropic
  SDK evolution plus one bug the 2024 draft itself never got past (per §3, "that draft
  still carried two further bugs"):
  - `role="tool"` → `role="user"`, and `tool_call_id=` → `tool_use_id=` in
    `ToolResultBlockParam` — the two bugs the 2024-09-11 draft still had, which would
    have 400'd at the API boundary even if that draft had been committed as-is.
  - The streaming path's `stream.messages[-1]` — never valid against a real SDK
    response object, and no longer present as an attribute in the current SDK at
    all — replaced with `stream.get_final_message()`.
  - One bug present in *every* historical and drafted version of this file, 2024
    draft included: the assistant's `tool_use` turn was never appended back into
    `messages` before the follow-up `tool_result` was sent. Verified live against
    the real API (2026-07-14): sending a `tool_result` without the preceding
    `tool_use` turn in history returns `400 invalid_request_error` — *"Each
    `tool_result` block must have a corresponding `tool_use` block in the previous
    message."* Fixed by appending `MessageParam(role="assistant", content=...)`
    (the full response/`final_message` content) before appending the tool results,
    and by batching all of a turn's tool results into one `user` message rather than
    one message per tool call.
  - Dependencies: `anthropic` bumped from `^0.34.2` to `^0.95.0`; the `httpx<0.28`
    compatibility pin (added 2026-07-05, commit `ef45975`) dropped as unnecessary
    against the current SDK.
  - Model ID: the retired `claude-3-sonnet-20240229` replaced with
    `claude-haiku-4-5-20251001` (cheap, current, sufficient for this tool's CRUD-tool
    workload).

**Smoke test, live against the real Anthropic API (2026-07-14), trivial spend (a
handful of Haiku calls):** in a scratch project directory, `submit` was run once
non-streaming and once with `--stream`, each asking Claude to call `list_files` and
report what it found. Both completed the full round trip — tool call issued, tool
result correctly returned to the model, coherent final reply — with **no
hallucination**: the model's answer matched the real directory contents exactly
(one file, then two, as files were added between runs). This is the same
`list_files`-driven round trip that produced hallucinated file listings and an
unbounded resubmission loop in the 2024-era `conversations/HelloWorld2.txt` runtime
evidence described in §4 — it now completes correctly on both the non-streaming and
streaming paths.

`bs.py` (the OpenAI-side bootstrap, §5) was out of scope for this pass and was not
touched.

## 10. Postscript 2 — same day, later: the 2024 mutation capability, verified

Scott ran a Codex-driven search of his own machine's disks (Google-Drive-synced
working tree and local archives; the search across all his computers/disks is NOT yet
complete). Findings on his machine **[SCOTT-SEARCH-VERIFIED — Codex-reported; the
cited files live on Scott's Mac, not in this repository]**:

- The Drive-synced working tree (`mysrc 2/ToGitHub/airproject/airproject.py`) has an
  **11:57 a.m. modification time on 2024-09-11** — the debugging revision immediately
  *before* the corrected ~12:00 conversation artifact; it still guesses `.tool_call` /
  `.tool_calls`. Reconstruction: Scott saved and ran the 11:57 revision, obtained the
  real `ToolUseBlock` trace at ~12:00, received the corrected file in chat — **and the
  corrected version was never saved over the working copy.** That is, precisely, how
  the fix was lost.
- A further Anthropic prototype, `new_bs.py`, could not have worked as saved
  (nonexistent constant import; `parameters` instead of `input_schema`; `tool_call`
  instead of `tool_use`; invalid `tool` message role) — recorded 400 errors in its
  history confirm.
- The SDK 0.34.2 requirements (`role` ∈ {user, assistant}; `tool_use_id`) are confirmed
  from the Drive-preserved SDK source itself (`types/message_param.py`,
  `types/tool_result_block_param.py`).

**Dynamic verification of the corrected 2024 artifact — run twice, independently:**
Codex (on Scott's machine) and Claude (on the VPS, from the archived conversation
`0f6afc41` — 2026-07-14) each extracted the corrected `handle_tool_use`, parsed it
(AST clean), and invoked it with a synthetic Anthropic-shaped `ToolUseBlock` requesting
`write_file(filename="probe.py", content="print(42)\n")`. Both runs:
`HANDLER_RESULT = Successfully wrote to 'probe.py'.` — file content verified. The same
artifact still constructs the tool result wrongly (`role="tool"`, `tool_call_id=`), and
the write happens *before* that invalid follow-up request is sent. So the likely 2024
behavior of the corrected version, had it been run: **Claude requests a write → the
local file changes → the follow-up API request fails.** Functioning mutation
capability; broken loop. (Local reproduction detail: the conversation contains ten
versions of `handle_tool_use`; exactly one is corrected. An early version invoked as a
negative control fails on `.tool_calls`, as expected.)

**The run timeline, decoded from the working dir's own artifacts** (conversations/
HelloWorld2.txt + its `~` backup; the tool stamped every run): Claude-path runs span
Sep 8 21:49 → Sep 11 **07:58** (ending in the blank-response burst). The corrected
artifact arrived in chat ~12:00 — four hours after the last recorded run. Mechanically,
a run of the corrected version would have left a post-noon timestamped entry in a
conversation file *before* failing at the tool-result return, and a write test would
have left its target file; neither exists. Together with the delivery conversation
ending without a pasted follow-up error, and the Sep-16 commit reverting to the wrong
pattern, the evidence leans strongly toward the corrected version never having been run
in any located working directory. (Scott's contemporaneous workflow — code written in
chat, copied out, run — makes a run in some never-located directory possible; the claim
stays INDETERMINATE, but every place a run would have left marks has none.)
**[RUNTIME + COMMIT + CONVERSATION, cross-referenced; added same day]**

**Revised bottom line for the Anthropic path** (refining §8, Codex's formulation,
adopted): *"AIRproject was run against the Anthropic API and reached genuine Claude
tool-use requests. A corrected Anthropic implementation produced during that work would
successfully execute a requested file write, although it would then fail when returning
the tool result. No surviving trace yet proves that Claude historically requested and
completed a mutating tool call."* The commit titled "Bootstrap is able to read and
write target file" remains OpenAI evidence (its `bs.py` imports OpenAI).

## 11. Postscript 3 — the M4 census and two corrections

Scott's Codex search of his M4 Mac Mini (2026-07-14, evening) completed the copy census
for that machine **[SCOTT-SEARCH-VERIFIED; the decisive pCloud logs independently
re-inspected on the VPS via its pCloud mount]**:

- **Copies located:** the pCloud working dir (richest — untracked histories, backups,
  test artifacts), a near-duplicate Google Drive workspace (`ToGitHub/airproject`,
  including the 11:57 pre-fix revision of §10), the older standalone Drive snapshot, a
  clean 2025 GitHub clone on a removable drive, and the GitHub repo itself — one branch,
  no unreachable objects, no Time Machine snapshots; later commits are docs/deps/security
  only. No further checkout on the internal disk.
- **The OpenAI-path write is conclusively evidenced and model-identified:** GPT-4o chose
  `write_file` in response to "Let's test writing. Can you write something to
  test_file.txt?", and `test_file.txt`'s modification time matches the logged event to
  the second (`airproject_history.json~` + `test_file.txt`). A read of `target.py`
  through the loop is equally evidenced (`airproject_history.json`). Immediately after
  each success, a history-reloading bug (a `function` message losing its `name` on
  reload) killed the next run — fixed in a later `bs.py` revision.
- **Correction 1 — self-modification, downgraded.** An earlier reconstruction described
  the OpenAI loop as "evolving its own code across several iterations." Direct
  re-inspection of `airproject_history.txt` shows: the design is explicitly
  self-targeting (`TARGET_FILE = sys.argv[0]  # The current script is the target file`),
  the loop READ its own source, and GPT-4o replied with a proposed revised version of
  the script — **in message text**. No `write_file` event ever carried a self-revision.
  Proven loop writes: `test_file.txt` only.
- **Correction 2 — no Claude-directed write, reproduced independently.** No surviving
  evidence anywhere of a Claude-directed file write; the recovered Sept-11 pCloud
  `airproject.py` handler returns `None` on the real recorded `ToolUseBlock` (reproduced
  offline by Codex, consistent with §10's dual verification of the corrected artifact).
- **The symmetry, for the record:** on both vendor paths, the improvement reached
  message text and died before persistence — Claude's corrected file was never saved
  over the 11:57 working copy (§10), and GPT-4o's self-revision was never written by the
  loop (this section). Both times the missing piece was the persistence step, not the
  model's contribution.
- **Maximally defensible README formulation** (Codex's, endorsed): *"An OpenAI-based
  bootstrap successfully read and wrote files on request. The later Claude MVP could
  exchange messages and reached tool use, but its filesystem-tool handling remained
  unreliable."*
