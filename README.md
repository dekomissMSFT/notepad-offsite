# Offsite: Build a Note-Taking App

**Demos:** Friday team meeting | **Teams:** Solo, pairs, or small groups | **Stack:** Anything

## What

Build the **weirdest note-taking app you can**. Must run locally. That's it.

"Note-taking app" is the seed — what you build doesn't have to resemble one. Wackier = better.

**You're the product owner.** Copilot is your engineering team. You set the vision, file issues, review output. Focus on *what*, not *how*.

## Goals

1. **Build something weird** — if it exists already, take it somewhere nobody expects.
2. **Be the PM** — break your vision into tasks, direct agents to execute.
3. **Learn something new** — new stack, new tool, new technique.
4. **Demo Friday** — you have all week to iterate.

## Agent Setup

Set up agents with different roles. Staff a small team.

- **Coder agent** — builds features, scaffolds project, writes code.
- **Tester agent** — give it OS access (screen, mouse, keyboard). It launches your app, clicks through UI, takes screenshots, catches runtime bugs. Code generator → QA engineer.

### Workflow

1. **You** file issues describing features
2. **Coder agent** picks issues, writes code, opens PRs
3. **Tester agent** pulls branch, launches app, verifies it works
4. **You** review, merge, file follow-ups
5. Repeat all week

### Autopilot mode

Run agent on a loop — it checks issues and works through them:

```bash
copilot -p "Check open issues. Pick one, fix it on a branch, open a PR." \
  --autopilot --allow-all
```

How [QuickSheet](https://github.com/cemheren/QuickSheet) was built — agent on schedule, picking issues, shipping PRs. Human reviews and merges.

## Ideas

[QuickSheet](https://github.com/cemheren/QuickSheet) turned desktop wallpaper into an interactive spreadsheet — notes, commands, live data in a grid. Backed by CSV. That energy.

- Notes in your terminal prompt
- Note app where UI is a game
- Notes stored as git commits
- Note app that only accepts drawings
- Keyboard macro pad that types your notes
- Notes that slowly fade away
- Note app that talks back
- 3D note space like a video game
- Notes that spread across filesystem like a virus
- Desktop wallpaper that IS your notes
- Note app controlled by hand gestures
- Something nobody thought of yet

## Getting Started

1. Clone this repo
2. Pick stack:

   | Approach | Examples |
   |----------|----------|
   | Desktop | Electron, Tauri, .NET MAUI, JavaFX, Tkinter |
   | Web (local) | React, Vue, Svelte + local storage |
   | Terminal | Go, Rust, Python (Rich/Textual), Node.js |
   | Mobile | React Native, Flutter, Swift, Kotlin |
   | Extension | Obsidian plugin, VS Code extension |

3. Create `projects/<your-name>/`
4. Build. Commit often.
5. Drop notes or screenshots in your project folder.

## Demos

**Friday team meeting.** Show app, show agent setup, share what surprised you. No slides.

---

*Previous offsite: [One Billion Row Challenge](https://github.com/gunnarmorling/1brc)*
