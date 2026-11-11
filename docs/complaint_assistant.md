# Complaint Assistant

The complaint endpoint applies conservative keyword matching to synthetic example category names and identifies only district names present in the supported entity catalogue. It does not infer a responsible department or urgency. It returns an editable title/description draft, missing-information prompts and official GHMC/Prajavani links.

Draft text is checked for common sensitive-data patterns and processed in memory. The citizen can edit it, copy it, or explicitly save it as a browser-local preparation task. A copy or saved task is not submission. Complaint text is not sent to an official portal by CivicSathi. Categories are examples from synthetic data and may differ from the official portal taxonomy.

Official destinations and source dates are shown from the configured source records. If location scope is unclear, the citizen should confirm which local body serves the address. Current policies and channel details must be checked on official pages.
