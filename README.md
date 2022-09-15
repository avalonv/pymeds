# pymeds

### Work In Progress

Basic CLI program to keep track of medication routines.

I wrote this when I was taking like 6 different medications a day and had a very terminal centric workflow, where it made sense to do with everything with a CLI script. Nowadays I have little use for this, but if I were to redesign it I would probably use an actual GUI (or at least a TUI) with a crontab service to send notifications.

### Usage:

```
[C]ommand followed by one or more meds, which are represented by numbers.
Ex: 't 0 1 q' will mark meds with numbers zero and one as [t]aken and quit.
'*' can be used to select all meds at once.
A check mark is displayed when all doses have been taken for the day,
otherwise the time since the most recent dose was taken is shown.
```
