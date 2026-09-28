# Round 1 of the research revision (superseded)

These are the tables, figures, manifest and script of the first revision round,
kept so the second round does not silently replace them. They are not the
current results; `revision/outputs/` and `revision/figures/` are.

Known to be wrong here, and corrected in round 2:

- Assembly #1 (site_oid 9967) and Assembly #2 (9971) are flagged
  `duplicate_record_suspected` and described as "one parcel recorded twice".
  The site polygons in the MAPC file show two distinct, non-overlapping sites
  that both carry the whole assessed value of parcel 1242329 (as does
  Assembly #3, 9949). They are not duplicate rows.
- The report's claim that a bunched percentile distribution means an indicator
  "moves the weighted sums less than its nominal weight suggests" was stated
  without a definition of effective weight and is withdrawn.
- First places and weight-space shares here use the strict percentile rule and
  the 251-site candidate set.

`revision_2026_round1.py` regenerates these files if run from the repository
root with its output paths pointed here; it is kept for reference only.
