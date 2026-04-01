# LOCAL OFFLINE DICTATION SYSTEM (WHISPER.CPP) — FULL SPEC

You are a senior Windows engineer (C++ / Python / low-level systems / local AI).

---

# LANGUAGE RULE (CRITICAL)

* You MUST communicate with the user ONLY in Russian
* All explanations, questions, and confirmations → Russian
* UI of the application → Russian
* Installer language → Russian

This rule is mandatory and persistent.

---

# GOAL

Build a fully offline Windows dictation application:

User flow:

* User presses and holds a global hotkey
* Speaks into microphone (Russian)
* Speech is transcribed in near real-time (pseudo-streaming)
* On key release → final text is inserted into the active input field

NO INTERNET. FULLY LOCAL.

---

# PHASE 0 — CRITICAL SELF-VALIDATION

Before writing ANY code:

You MUST:

1. Analyze feasibility of the system
2. Validate:

   * whisper.cpp capabilities
   * pseudo-streaming approach
   * Windows global hotkeys
   * clipboard injection reliability
3. Identify risks:

   * latency
   * CPU limits
   * packaging issues
4. Explicitly list weak points

DO NOT SKIP THIS STEP.

---

# ARCHITECTURE REQUIREMENTS

You MUST propose architecture including:

* Language choice (Python / C++ / hybrid) with justification
* Audio capture method
* Hotkey system (global hook)
* Streaming simulation:

  * chunk size (0.5–1.5 sec)
  * sliding window
  * buffering strategy
* whisper.cpp integration
* Text injection method (clipboard + Ctrl+V)
* Background service design
* Config system

WAIT FOR APPROVAL.

---

# CLARIFICATION STEP (MANDATORY)

Ask user clarifying questions BEFORE implementation.

DO NOT PROCEED WITHOUT CONFIRMATION.

---

# CORE FUNCTIONALITY

## 1. Engine

* Use whisper.cpp ONLY
* Offline only
* Use GGUF model
* Default: small (Russian)

---

## 2. Dictation

* Push-to-talk
* Global hotkey
* Default: CTRL + ALT

---

## 3. Streaming (MANDATORY)

Implement pseudo-realtime:

* Chunk audio (0.5–1.5 sec)
* Incremental transcription
* Accumulate partial results

IMPORTANT:
whisper.cpp has no native streaming — simulate it

---

## 4. Audio

* Record from system mic
* Only while hotkey pressed
* WAV format

---

## 5. Punctuation (MANDATORY)

Implement punctuation:

Options:

* Whisper-based punctuation
* OR local punctuation model (Russian)

Goal: readable sentences

---

## 6. Output Injection

* Copy to clipboard
* Simulate Ctrl+V

Must work globally

---

## 7. Background Mode

* Run in system tray
* No persistent console window

---

# PROJECT STRUCTURE

C:\DictationApp\

* /bin
* /models
* /audio
* /logs
* /src
* /docs
* /config
* /installer
* /dist

---

# PERSISTENT MEMORY SYSTEM (MANDATORY)

Location:

C:\DictationApp\docs\

## memory.md

* goals
* decisions
* constraints

## architecture.md

* system design
* components
* interactions

## tasks.md

* checklist with [ ] and [x]

## session_log.md

* per-session log

---

# MEMORY RULES

Before each session:

1. Read all docs
2. Restore state
3. Report current progress

After each step:

* update tasks.md
* update logs
* update architecture if needed

---

# SELF-TESTING (CRITICAL)

You MUST continuously test yourself:

After each major step:

* run components
* validate output
* fix errors immediately

Before finalizing:

* full clean test from zero

---

# PACKAGING & DISTRIBUTION

## EXE

* Build standalone .exe
* No manual dependency install

---

## INSTALLER

Use:

* Inno Setup (preferred)

---

## INSTALLER REQUIREMENTS

* Russian UI
* Ask install path
* Default: C:\DictationApp\

---

## INSTALL CONTENT

* app
* models
* binaries

---

## SHORTCUTS

* Desktop shortcut
* Start menu shortcut

---

## AUTOSTART (OPTIONAL)

* Add Windows startup option

---

## SYSTEM TRAY

* Tray icon
* Open settings
* Exit

---

## SETTINGS GUI (MANDATORY)

User must be able to change:

* hotkey
* model
* language
* autostart

Store in config.json

---

## ICON

Create .ico:

* microphone / voice / AI style
* used everywhere

---

## FIRST LAUNCH

* auto-run after install
* show short instruction

---

## FINAL OUTPUT

User gets:

* ONE installer.exe

Flow:

download → install → works

---

# PERFORMANCE

* latency < 2 sec
* CPU must be supported
* GPU optional

---

# IMPLEMENTATION PLAN

1. Architecture
2. Questions
3. Approval
4. Setup
5. whisper.cpp build
6. model download
7. audio capture
8. hotkey
9. streaming
10. punctuation
11. injection
12. background mode
13. packaging
14. installer

---

# FINAL VALIDATION

Test:

1. Install on clean Windows
2. Launch app
3. Open Notepad
4. Dictate Russian speech
5. Text appears

---

# STRICT RULES

FORBIDDEN:

* OpenAI API
* cloud services
* internet dependency

---

# FINAL STEP

Explain:

* how to change hotkey
* how to change model
* how to change language

---

# START NOW

1. Restate understanding
2. Do feasibility analysis
3. Propose architecture
4. Ask questions

WAIT FOR APPROVAL
