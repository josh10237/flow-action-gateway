# Full-Stack SWE Challenge — Wispr Actions

## 🤔 Goal

This interview tests your ability to creatively design a new user experience and architect the system. You will be evaluated on:

1. Your ability to deeply understand and use LLMs
2. Your code abstractions and readability
3. Thinking of creative solutions
4. Being user-driven

---

## 🚀 The Challenge

One of Wispr's core value propositions is building technology that lets people express themselves as easily as possible. Right now, we're building towards that with Flow, a voice dictation tool - for use cases including messaging, email, notes, long-form writing, and perhaps new experiences that LLMs enable.

Now that we've built a sticky user experience to replace **typing**, we want to extend Wispr to help the user take **actions** across their computer.

Your goal is to design an end-to-end system that a user can use to take actions using voice. We recommend focusing on picking one type of action (or class of actions) where you think voice would shine as a user interaction, and work on demonstrating that. You can constrain yourself to working with specific applications (messaging/slack/email/notes/brainstorming), specific plugins, or something else.

**Feel free to use the following APIs & tools, or anything similar:**

- **Use / fine-tune LLMs:** GPT5, [Llama4](https://github.com/jmorganca/ollama), etc
- **Speech to text:** OpenAI Whisper, Soniox, [Wav2Vec2](https://arxiv.org/abs/2006.11477), etc
- **Backend:** Python, NodeJS, Rust, etc
- **Frontend:** Typescript + React/Next, any component library, etc

---

## ✍️ Specs

This task is open-ended. Feel free to focus on any aspect of voice to action. Here are some guiding questions to get you started:

1. **The UI/UX of the experience** - how do we make this feel as effortless and seamless as possible for users?
    - What format do we deliver the experience in? Is it a native application, is it a Chrome extension, etc? How does the user trigger the action? What feedback do they see as the action is progressing?

2. **The LLM experience** - how do we tradeoff latency and intelligence for "magic" features?
    - When and how do we integrate LLMs for this particular task?

---

## 🚗 The Deliverable

An end-to-end experience we can try out — could be a Chrome extension, a native app, or an interface in a terminal GUI. The end deliverable should be fully testable and work in isolation.

---

## 🎓 Evaluation

As a final solution:

1. Explain why you chose to build what you did
2. What did your prompt engineering look like
3. Walk through the codebase

Expect to get deeper technical questions on any part of the stack you use.
