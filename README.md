
````markdown
# Universal React-to-Angular Transpiler

## What is this tool?
This is a Python script that reads your React components, figures out the logic (like state variables and functions), and rewrites them
into a working Angular component (TypeScript + HTML) using Regex

---

## Architecture Design
The logic is linear and simple to debug. We ingest the file, break it down, swap the syntax, and write the new files.




+-----------------------+        +---------------------------+        +-----------------------+
|   INPUT               |        |   PROCESSOR (Python)      |        |   OUTPUT              |
|   React File (.jsx)   |        |                           |        |   Angular Files       |
+-----------------------+        +---------------------------+        +-----------------------+
           |                                  |                                   |
           v                                  v                                   v
   +----------------+            +-------------------------+            +-------------------+
   |  Raw Text      |----------->|  1. EXTRACTOR           |----------->|  Component.ts     |
   |                |            |  (Finds Patterns)       |            |  (The Logic)      |
   +----------------+            +-------------------------+            +-------------------+
                                              |
                                              v
                                 +-------------------------+            +-------------------+
                                 |  2. TRANSLATOR          |----------->|  Component.html   |
                                 |  (Rewrites Syntax)      |            |  (The View)       |
                                 +-------------------------+            +-------------------+
````

-----

## Project Structure (The Plan for V2)

Right now, this is a single script for the demo. But for a production app, I’d refactor this using a **Feature-Based** structure. This keeps things clean—if you break the event handlers, you don't accidentally kill the state logic.

```text
/transpiler
    /parsers/            <-- Logic for distinct React features
        hooks.py         <-- Handles useState, useEffect
        events.py        <-- Handles onClick, onChange
        conditionals.py  <-- Handles ternary operators ( ? : )
        loops.py         <-- Handles .map() lists
    /generators/         <-- The code writers
        angular.py       <-- Assembles the final .ts and .html
    /tests/              <-- QA
        test_hooks.py
        test_events.py
    main.py              <-- The entry point
```

-----

## Design Choice: Why Regex?

Speed: I needed to prototype this quickly. Setting up a full parser takes a lot of config.

Beginner Friendly: It relies on matching text patterns rather than deep React knowledge. You do not need to understand complex AST node types or React internals to read and modify this script.

No Bloat: This runs with standard Python libraries—no npm install required.

-----

## Feature Support Matrix

 optimized for the "Happy Path"—the most common patterns you see in daily work.

| Feature | Supported (Ship it) | Unsupported (Needs Manual Fix) |
| :--- | :--- | :--- |
| **State / Hooks** | `useState` only. | `useEffect`, `useContext`, or custom hooks. |
| **Lists** | `.map()` (Becomes `*ngFor`). | `.filter()`, `.reduce()`, or chained stuff. |
| **Logic** | Arrow Functions (`const x = () => {}`). | Regular `function` keyword or Async/Await. |
| **Events** | `onClick` (Becomes `(click)`). | `onSubmit`, `onHover`, etc. |

-----

## Limitations & "Battle-Tested" Scenarios

Some Edge Cases that occurs in a common react development workflow

| Scenario | The Problem | The Fix |
| :--- | :--- | :--- |
| **Missing Lifecycle** | We ignore `useEffect` right now. Angular does side effects in `ngOnInit`, which is a totally different beast. | **Plan:** Capture the `useEffect` body and inject it into an `ngOnInit()` method automatically. |
| **Complex Logic** | If you chain methods like `items.filter(...).map(...)`, the regex gets confused because it expects a simple list. | **Plan:** Use an AST to understand method chaining and turn filters into Angular Pipes. |
| **Conditional UI** | React uses `{ isOpen && <Modal /> }`. Angular needs `<div *ngIf="isOpen">`. Regex struggles to find the closing bracket. | **Plan:** We need a recursive parser to find the matching `}` so we can wrap the HTML correctly. |

-----

## Fallback Strategy (Failing Gracefully)

If the tool hits a block of code it doesn't understand (like a complex `.filter()` chain), it won't crash.

Instead, it just comments out that block and adds a "TODO" flag so we can trace un-automatable codeblocks.

```typescript
/* [!] AUTOMATION FALLBACK: Manual Conversion Needed 
   Original Source:
   visibleItems.filter(item => item.isActive)
*/
```

-----

## Future Scope: The AST Pipeline

To make this production-ready, we need to move away from text matching and start using an **Abstract Syntax Tree (AST)** Which can handle complex Cases as well.

**The Flow:**

1.  **Parse (React AST):**
    We read the code and turn it into a tree structure. The tool stops seeing "text" and starts understanding that `useState` is a *Hook*.
2.  **Transform (Mapper):**
    We convert the React tree into an Angular tree. We map the "React Hook" nodes directly to "Angular Class Property" nodes.
3.  **Generate (Angular Code):**
    We feed that new Angular tree into a generator that prints out perfectly valid TypeScript code.

-----

## How to Run

1.  Drop your file in `react/`.
2.  Run the script:
    ```bash
    python transpiler.py
    ```
3.  Check `output/` for your new code.

<!-- end list -->

```
```
