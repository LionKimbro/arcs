# ChronoMark
Created: 2026-10-11
Modified: 2026-10-11

## Purpose
Created: 2026-10-11
Modified: 2026-10-11

ChronoMark is a small protocol and Python runtime for representing time in ordinary JSON without pretending uncertain dates are exact. It preserves approximate, remembered, reconstructed, disputed, and unknown temporal information, including the reasoning behind it. Lion has selected it for Arcs' uncertain times and related temporal representation. The repository is `F:\repo\chronomark`, recorded in [the filesystem location registry](../../db/file-system-locations.json).

## Core model
Created: 2026-10-11
Modified: 2026-10-11

An EVENT or PERIOD record has a canonical UUID, zero or more temporal claims, and an optional working temporal claim. Each claim has its own UUID and describes a perspective on when the event happened or the period began and ended. Multiple claims can preserve disagreement rather than erase it. The working claim is the operational choice for display, sorting, filtering, and timeline placement; it is not a declaration of proven truth. Without an explicit working choice, a sole claim is used, but multiple unresolved claims are not silently reduced to one.

Time points can carry `earliest`, `focus` (the best estimate), `latest`, and `precision`, from year through microsecond. Period boundaries can also express UNKNOWN or ONGOING. Claims can include confidence, evidence basis, claimant, and explanatory `claim-notes`; sparse or explanation-only claims are valid. `what-happened` describes the event or period, while `claim-notes` explains the temporal assertion.

Record registration and claim recording timestamps describe when data entered the system, not when the life event happened. Calendar values use the inherited explicit timezone; timestamps with times of day carry an offset or Z. The host computer's timezone must not be silently substituted.

## Relevance to Arcs
Created: 2026-10-11
Modified: 2026-10-11

ChronoMark's PERIOD and EVENT distinction offers a natural conceptual fit for [arcs](arc.md) and [events](event.md). Its uncertain boundaries allow an arc to begin gradually, end approximately, or remain ongoing without forcing invented precision. How Arcs objects and ChronoMark records share or reference identities is not yet decided. The choice of ChronoMark does not settle Arcs' internal storage format.

## Sources and review scope
Created: 2026-10-11
Modified: 2026-10-11

This is a brief orientation from the README, the newer human guide `docs/raw/010__chronomark-human-guide.md`, the opening of `012__chronomark-ai-coding-agent-guide.md`, and the metadata and orientation of `011__chronomark-softspec.json` (draft SoftSpec v2). The README's current-artifact list points to older 006–008 documents; this note uses the newer 010–012 set. Implementation behavior and integration have not been audited.
