# Offsite: Build a Note-Taking App

**Time:** Offsite kickoff + one week to iterate | **Demos:** Friday team meeting | **Teams:** Your choice (solo, pairs, small groups) | **Stack:** Anything goes

## The Exercise

Build the **weirdest, most creative note-taking app you can imagine**. The only constraint: it runs locally on your machine.

"Note-taking app" is just the seed. What you build doesn't have to look, feel, or behave like any note-taking app that exists. The wackier the better.

**Your role: product owner.** Think of Copilot as your engineering team. You have the vision — describe what you want, architect the direction, and let AI agents do the heavy lifting. Focus on *what* to build, not just *how* to build it.

## Goals

1. **Build something weird** — if it already exists, push it in a direction nobody would expect.
2. **Think like a PM, not a coder** — have a vision, break it down, and direct Copilot to execute it. Use agent mode, multi-file edits, iterate on the output.
3. **Learn something new** — pick a stack, tool, or technique you've been curious about.
4. **Have something to demo** — demos are at the Friday team meeting. You have the full week to keep iterating after the offsite.

## Setting Up Your Agent Team

Think of this like staffing a small team. You can set up multiple agents with different roles, and give them the access they need to do their jobs.

### Suggested agent roles

- **Coder agent** — builds features, scaffolds the project, writes new code. This is the default Copilot experience.
- **Tester agent** — runs the app, checks that features actually work, files issues when they don't. Give this agent OS access so it can launch your app, interact with the UI, take screenshots, and verify behavior end-to-end.

### Giving agents OS access

Agents are more useful when they can see and interact with what they're building. With OS-level access (screen, mouse, keyboard), a tester agent can:

- Launch your app and verify it starts correctly
- Click through the UI, type into inputs, test workflows
- Take screenshots to confirm visual output
- Catch bugs that only show up at runtime

This turns your agent from a code generator into something closer to a QA engineer.

### Example workflow

1. **You** define the vision and file issues
2. **Coder agent** picks up issues, writes code, opens PRs
3. **Tester agent** pulls the branch, launches the app, verifies the feature works
4. **You** review the results, merge what's good, file follow-up issues
5. Repeat all week — demos are Friday

## Ideas

[QuickSheet](https://github.com/cemheren/QuickSheet) turned the desktop wallpaper into an interactive spreadsheet — notes, runnable commands, and live data all in a grid behind your windows. Backed by a plain CSV file. That's the kind of energy we're going for.

Some sparks to get you thinking:

- Notes that live in your terminal prompt
- A note app where the UI is a game
- Notes stored as git commits
- A note-taking app that only accepts drawings
- A physical keyboard macro pad that types your notes
- Notes that are ephemeral and slowly fade away
- A note app that talks back to you
- A 3D note space you navigate like a video game
- Notes that spread across your file system like a virus
- Desktop wallpaper that IS your notes
- A note app controlled entirely by hand gestures
- Something no one has thought of yet

## Getting Started

1. **Clone this repo.**
2. **Pick your stack.** Some ideas:

   | Approach | Examples |
   |----------|----------|
   | Desktop app | Electron, Tauri, .NET MAUI, JavaFX, Tkinter |
   | Web (local) | React, Vue, Svelte + local storage or a local API |
   | Terminal | Go, Rust, Python (Rich/Textual), Node.js |
   | Mobile | React Native, Flutter, Swift, Kotlin |
   | Extension | Obsidian plugin, VS Code extension, Raycast extension |

3. **Create a directory** for your project: `projects/<your-name>/`
4. **Build.** Commit often so you can backtrack easily.
5. **Document** what you built — drop a few notes or screenshots in your project folder.

## Showcase

Demos are at the **Friday team meeting**. Show what you built, how your agent setup worked, and what surprised you. No slides — just show the app.

## Going further: agent on autopilot

If you want to take the PM role further, try setting up an agent that works autonomously. File issues on your repo describing what you want, then let Copilot loop through them:

```bash
copilot -p "Check open issues on this repo. Pick one, fix it on a branch, and open a PR." \
  --autopilot --allow-all
```

You write issues, the agent writes code, you review PRs. This is how [QuickSheet](https://github.com/cemheren/QuickSheet) was developed — an agent running on a schedule, picking issues and shipping PRs while the human just reviews and merges.

---

*Previous offsite: [One Billion Row Challenge](https://github.com/gunnarmorling/1brc)*
