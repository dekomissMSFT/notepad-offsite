# 📝 Offsite Challenge: Build a Note-Taking App with AI

**Time:** ~3-4 hours | **Teams:** Your choice (solo, pairs, small groups) | **Stack:** Anything goes

## The Challenge

Build a **local-first note-taking app** — no cloud, no accounts, just a tool that runs on your machine and helps you capture and organize thoughts. Use AI (Copilot, ChatGPT, Claude, Cursor, whatever) as your primary development accelerator.

The twist: **you decide what "note-taking" means.** A simple markdown editor? A Zettelkasten with backlinks? A voice-to-text scratchpad? A terminal-based daily journal? A canvas with spatial notes? Go wherever your curiosity takes you.

## Goals

1. **Ship something usable** — by the end of the session, your app should actually work. You should be able to create, view, and manage notes.
2. **Learn by building** — experiment with a stack, tool, or technique you're curious about.
3. **Push AI-assisted development** — see how far you can get in a few hours when you lean hard on AI tooling.

## Challenge Tiers

Pick a tier as your baseline target, then stretch if time allows.

### 🥉 Bronze — The Basics (~1-2 hours)
- [ ] Create, read, update, delete notes
- [ ] Notes persist locally (file system, SQLite, whatever)
- [ ] Some kind of UI (CLI counts!)

### 🥈 Silver — Make It Yours (~2-3 hours)
Everything in Bronze, plus **one or more** of:
- [ ] Search / filter notes
- [ ] Markdown rendering
- [ ] Tags or categories
- [ ] Keyboard-driven workflow
- [ ] Import/export (JSON, Markdown files, etc.)

### 🥇 Gold — Show Off (~3-4 hours)
Everything in Silver, plus **one or more** of:
- [ ] Backlinks / note graph / wiki-style linking
- [ ] AI-powered features (summarization, auto-tagging, semantic search)
- [ ] Rich text or block-based editing
- [ ] Plugin or extension system
- [ ] Real-time preview
- [ ] Multi-window or split-pane UI
- [ ] Version history / undo timeline

### 💎 Diamond — Legend Status
Surprise us. Some wild ideas:
- Voice-to-note with local whisper model
- Spatial canvas (think Miro meets notes)
- Git-backed version control for notes
- Local RAG over your own notes
- Collaborative editing (local network)

## Getting Started

1. **Fork or clone this repo** — or start fresh in your own directory, up to you.
2. **Pick your stack.** Here are some ideas (not requirements):

   | Approach | Stack Ideas |
   |----------|------------|
   | Desktop app | Electron, Tauri, .NET MAUI, JavaFX, Tkinter |
   | Web (local) | React/Vue/Svelte + local storage or a local API |
   | Terminal | Go CLI, Rust CLI, Python + Rich/Textual, Node.js |
   | Mobile | React Native, Flutter, Swift, Kotlin |
   | Unconventional | Obsidian plugin, VS Code extension, Raycast extension |

3. **Create a directory** for your project: `projects/<your-name>/`
4. **Build!** Lean on AI. Prompt aggressively. Iterate fast.
5. **Document** what you built — drop a few sentences or screenshots in your project folder.

## Tips for AI-Assisted Development

- **Start with a conversation.** Describe what you want to build before writing code. Let the AI help you architect.
- **Go wide, then deep.** Scaffold the full app first, then iterate on features.
- **Copy-paste errors back.** AI is great at debugging when you give it the full context.
- **Don't fight the AI's suggestions too hard** — if it wants to take you in an interesting direction, follow it and see what happens.
- **Commit often.** You'll want to be able to revert if an AI-generated change breaks things.

## Showcase

At the end of the session, we'll do a quick round of demos. Show what you built, what worked, what was surprising. No slides needed — just show the app and talk about the journey.

## Ground Rules

- **No judgment on stack choices.** Notepad in Bash? Respect.
- **AI is encouraged, not required** for every line — but push yourself to use it more than you normally would.
- **Have fun.** This is an offsite, not a sprint.

---

*Previous offsite: [One Billion Row Challenge](https://github.com/gunnarmorling/1brc) — this time we're moving up the stack.*
