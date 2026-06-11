# Mini-Me

**The infrastructure of ambition for people without mentors, money, or network.**

Mini-Me is a personal AI operating system for ambitious emerging-market students and builders. V1 is a small Python CLI that helps Simon answer one question every day:

> What is the highest-value thing I should do right now?

Mini-Me is not a generic chatbot or a pretty productivity app. It is a local feedback loop:

Observe -> Reflect -> Learn -> Improve

## Install

From this folder:

```powershell
cd mini-me
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On macOS or Linux:

```bash
cd mini-me
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure the API Key

Mini-Me uses environment variables so the LLM provider can be swapped later.

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```text
MINIME_LLM_PROVIDER=openai
MINIME_LLM_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your_api_key_here
```

If no API key is set, `/plan` still works: it falls back to a local deterministic planner that ranks open tasks using your current focus in `goals.md`, always deprioritizes research-flavored tasks, caps the plan at 3 actions, and tells you to execute them in order. Pattern warnings are shown in both modes. Setting a real API key upgrades `/plan` to a full LLM plan.

## Run

```powershell
python main.py
```

## Commands

- `/plan` - generate today's 3 highest-value actions
- `/post` - draft a build-in-public X post from completed work
- `/patterns` - detect repeated blockers, lessons, and tomorrow rules
- `/add-task` - add a new task
- `/show-tasks` - show current tasks
- `/done` - mark an open task complete
- `/review` - review the day and store lessons
- `/exit` - quit

## Example Usage

```text
mini-me> /show-tasks
1. [ ] Finish KCA assignment - SCHOOL
2. [ ] Build Mini-Me V1 - PROJECT

mini-me> /done
Open tasks:
1. Finish KCA assignment — SCHOOL
2. Build Mini-Me V1 — PROJECT
Mark which task done? 2
Done: Build Mini-Me V1 — PROJECT

mini-me> /review
Daily review. Be honest and concrete.
1. What did you complete today? Built the first CLI loop.
2. What blocked you? Too much tool research.
3. What did you learn? The product gets useful when memory updates.
4. What should change tomorrow? Ship before browsing new frameworks.
Review saved. Memory updated with today's completed tasks, lessons, blockers, and tomorrow rules.

mini-me> /patterns
Analyzing recent reviews for repeated blockers, lessons, and tomorrow rules...
Detected 1 pattern(s):
- Pattern: Context switching appears repeatedly
  Evidence: Mentioned in 2 reviews as a blocker
  Suggested response: Start the day with one execution task before research
Memory updated under ## Patterns.
```

## Data Files

Mini-Me stores everything locally in markdown:

- `data/goals.md`
- `data/tasks.md`
- `data/memory.md`
- `data/reviews.md`

No database is used in V1.

Daily reviews are saved in full to `data/reviews.md`. Mini-Me also updates clean dated sections in `data/memory.md`:

- `Completed Tasks`
- `Lessons`
- `Recurring Blockers`
- `Tomorrow Rules`

`/patterns` reads `data/reviews.md`, detects repeated blockers, lessons, and tomorrow rules with local semantic grouping, then writes concise results under `## Patterns` in `data/memory.md`.

V2.1 groups different phrases into higher-level patterns. For example, `context switching`, `opening too many tabs`, `too many projects`, and `lack of focus` are treated as `Attention Fragmentation`.

Pattern results look like this:

```md
### Attention Fragmentation

Frequency: 4
Evidence:
- context switching
- too many tabs

Suggested Response:
Start with one execution task. Close unrelated tabs. Do not research until the first task is complete.
```

When `/plan` runs, Mini-Me reads `## Patterns` from memory and prints pattern warnings before the plan:

```text
=== Pattern Warnings ===

* Attention Fragmentation is recurring: Start with one execution task. Close unrelated tabs. Do not research until the first task is complete.
```
