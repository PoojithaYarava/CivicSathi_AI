# System Architecture

```mermaid
flowchart LR
  Citizen --> Browser[Static HTML/CSS/JavaScript]
  Browser -->|JSON over loopback| HTTP[Python standard-library HTTP server]
  HTTP --> Safety[Size, shape and sensitive-pattern checks]
  Safety --> Service[Application service]
  Service --> NLP[Intent, entities and TF-IDF search]
  Service --> CSV[Processed CSV catalogues]
  Service --> Checklists[Reviewed requirement CSV]
  Browser --> LocalStorage[Explicitly saved preparation tasks]
  HTTP --> Browser
  Browser --> Official[Government pages opened by citizen]
```

The backend owns catalogue access, input checks, query analysis and structured complaint draft preparation. The browser owns presentation, user-reviewed edits, optional browser speech, and tasks saved only after an explicit user action. No raw task data or complaint draft is written by the server. Browser local storage is visible to anyone using that browser profile, so sensitive information must not be put in task notes.

The application remains functional without external AI, embeddings, or speech APIs. Speech recognition is a browser capability, not a guaranteed local model; ask the user to read the disclosure before using it.
