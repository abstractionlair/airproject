# Air Project

As I started to rely more on LLMs to help with coding, I wanted something better than copying and pasting between chats in a web browser and my text editor.
At around the same time I had strted relying heavily on the Projects feature of Claude largely because it made it easy to save artifacts generated in a conversation to project knowledge.
With some manual help, this could emulate a small filesystem in which Claude could edit files (Claude writes a new version, I delete the old one) and this worked for small coding projects.
But it was cumbersome and when I learned about tool use, I thought it would be possible to do better by creating a command line chat tool that would access my filesystem via tools.
At the time I was also jumping back and forth between Claude, ChatGPT, and Gemini, pasting the same queries into each, or getting critiques of one's output by another.
So I thought this tool should also be multi-model.

Some initial attempts, at different times with help of different chat models, kind of worked in a formal way. I could send a message and get a response, maybe get a file read, etc.
But progress was slow and the LLM-written code tended to be buggy or convoluted.

One particular issue was that all of the LLMs had been trained on versions of the SDKs or sometimes APIs which were pretty out of date.
This led to a side project trying to get an LLM to write a good, one-page document of the Anthropic Python SDK from the source code.
This eneded up being Gemini (I don't recall the version) becuase the large context window made it much easier.
The results were not entirely useless, but I found that even sharing that document with the models it was hard to get them to use that knowledge rather than what they were trained on.

I decided to narrow the scope for an MVP.
This would be just Claude and using the API rather than the SDK since Claude's knowledge of that was less out of date.
We got a simple version working, sufficient to start testing.
While the plumbing worked, it just didn't work as well as Claude in the Claude Projects environment.
This led to me poking around and learning about the implementation of Claude Projects.
I had not known that all of project knowledge was inserted into Claude's context.
(Interestingly, neither did Claude. We found out together via experiments. "I just added XXX to project knowledge, do you see it? Where? ...")
I learned that this was critical to the performance I was getting the the projects environment.
There, Claude had an ambient awareness of what was in project knowledge.
In my implementation, Claude could read (and write) files if directed to, but didn't naturally go looking for things.
This makes sense in retrospect --- I hadn't given it any knowledge about what was in the files which would let it figure out when they were worth looking at.
There were potentially ways to move forward, such as a search tool or an index that would be automatically kept up to date, but I stopped here.

And now we have Claude Code.
