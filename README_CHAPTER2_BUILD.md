# POLS C1000 Chapter 2 Sim-Discussion Build

This is an engineering clone of the working Chapter 1 Sim with Chapter 2 architecture added.

## Added in this build
- Chapter 2 authoritative knowledge layer.
- Hidden balanced question pool: 1 accessible, 2 medium, 1 challenging target per run.
- Guest bench: James Madison, Henry Clay, Lyndon B. Johnson, Shirley Chisholm, John McCain.
- Period-prose rules and historical grounding guardrails for guests.
- Clarification is non-penalized and preserves the same academic target.
- Explicit skip/pass is permitted and marked as zero for that primary question.
- Dynamic guest routing by question target.
- Guest expression/voice hooks prepared for portrait assets.

## Guest image folders expected
`static/expressions/guests/<slug>/{neutral,amused,skeptical,thinking,surprised}.png`

The app currently falls back gracefully when a guest portrait has not yet been added.

## v0.2 guest integration
- Approved Chapter 2 room anchor installed as `static/chapter2_room.png`.
- Madison, Clay, LBJ, Chisholm, and McCain expression assets installed under `static/expressions/guests/`.
- Added explicit `smile` expression support alongside neutral, amused, skeptical, thinking, and surprised.
- Guest portraits are wired into the live dialogue portrait map.
