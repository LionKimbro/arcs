# Command Center
Created: 2026-10-11
Modified: 2026-10-11

## Established development interface
Created: 2026-10-11
Modified: 2026-10-11

During development, the program opens into the **Command Center** window. A large `tkinter.Text` area shows output. New output is appended below prior output, with the visible area advancing toward the newest output so older text moves upward like a terminal. A small `tkinter.Entry` beneath it receives input. Pressing Enter submits the entered text for processing by Core.

There is exactly one Command Center while the program runs. Startup opens it alone; it does not automatically open a set of Arc Detail windows. Command Center is a programmer's remote control, not the arc-reading interface. User actions in it create or summon detail views as described below.

“TK Enter.text” and “TK Enter.entry” in dictation are interpreted as `tkinter.Text` and `tkinter.Entry`.

## Ownership and interaction
Created: 2026-10-11
Modified: 2026-10-11

Tk presents both widgets and binds the input event. It passes the text as semantic event data to Core, where application interpretation and work are initiated. Core sends output instructions back through the dedicated Core-to-Tk queue. Tk renders those instructions in the output area; Tk itself performs no domain work.

Command grammar and available commands are not yet defined. Echo behavior, clearing the entry, command history, output editability, scrollback limits, and whether automatic scrolling pauses while reading older output remain open. This interface is the initial development surface, not a decision to replace the planned arc-detail views.

## Initial operations and on-demand windows
Created: 2026-10-11
Modified: 2026-10-11

The first slice needs text commands to create an arc, list persisted arcs, and open an existing arc by UUID. Help or a visible command summary must explain the chosen grammar. Creating an arc summons its Arc Detail window as the sensible result of that operation. Opening an existing arc summons a detail view of that UUID. Repeated user actions can produce several detail windows for the same or different arcs. Commands should report requests, results, identities, and errors in the output area.

Buttons are also allowed, but optional. A button and a text command initiating the same operation must enter the same Core semantic path rather than duplicate business logic in Tk. Exact command spellings, quoting rules, creation form details, and any button arrangement remain open for a small design pass. Do not introduce a shell, evaluate Python input, or expose SQL merely because the widget resembles a terminal.

## Lifetime
Created: 2026-10-11
Modified: 2026-10-11

Closing Command Center requests orderly shutdown of the entire application and all detail windows. It remains the lifetime anchor, not a disposable additional view. During shutdown, reject new work and preserve the event loop until the chosen save barrier permits destruction. See [lifecycle](lifecycle.md). Closing a detail window alone leaves Command Center and the application running.
