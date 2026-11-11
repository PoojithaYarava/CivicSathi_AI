# Voice Processing

The microphone control uses `SpeechRecognition` or `webkitSpeechRecognition` when available in the browser. The user starts each session; recognized words appear in the editable query box and are never submitted automatically. Interim transcript text is shown as it arrives. The UI distinguishes browser microphone activity, detected speech, and a speech service that returns no transcript. Permission denial, unsupported browsers, empty results, and recognition errors leave text input available.

Recognition offers English (India), Telugu, and Telugu + English. For the mixed option, the page uses the browser's Telugu (`te-IN`) recognition locale; the Web Speech API accepts a single recognition locale per session, so code-mixed accuracy is best-effort and users should review/edit the transcript. The mixed option is selected by default. No independent speech accuracy evaluation has been performed.

In Microsoft Edge, the standard Web Speech API uses Microsoft's speech service; an Edge policy can disable this API. The on-device recognition model described in current Edge developer documentation is limited to Edge Canary/Dev and a short language list that does not include Telugu. Therefore Telugu recognition depends on the browser speech service and can fail when the service is blocked, offline, or cannot recognize the audio. CivicSathi does not have a server-side or bundled local speech model fallback.

Speech output is a user-initiated browser `speechSynthesis` feature, with an explicit stop button. Voice features are optional enhancements, not a dependency for the app.
