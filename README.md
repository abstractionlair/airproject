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
an earlier OpenAI-based bootstrap script. Note the pinned `anthropic` SDK
(0.34.x) requires `httpx<0.28` — newer httpx removed an argument the older
SDK still passes at client construction.

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
