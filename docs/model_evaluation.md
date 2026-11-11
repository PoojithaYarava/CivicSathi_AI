# Model Evaluation

Detailed run metadata is stored in `models/nlp/intent_metrics.json`; the reproducible summary is `reports/nlp_evaluation_report.md`.

## Intent model

- Data: 1,296 synthetic, mechanically generated, balanced query examples (12 labels, 108 each; 432 each in English, Telugu, Telugu-English).
- Split: deterministic grouped split, seed 42; train 777, validation 260, test 259.
- Features: word TF-IDF 1-2 grams plus character TF-IDF 2-5 grams.
- Candidates: Logistic Regression and sigmoid-calibrated Linear SVM. Logistic Regression selected by deterministic tie order after equal validation macro F1.
- Held-out test: accuracy 1.000, macro precision/recall/F1 1.000, weighted F1 1.000, support 259.
- Language subsets: English n=88, Telugu n=84, Telugu-English n=87; each reports accuracy/macro F1 1.000 on this generated split.

These figures measure separation among repeated synthetic templates. They do not establish accuracy on real users, fluent-speaker quality, robustness to spelling variation, calibration quality, or fairness. Native-speaker-reviewed and independently authored evaluation sets are required before public performance claims.

## Entity extraction

Longest catalogue dictionary matches and conservative regex date extraction are implemented. No annotated gold entity spans exist; precision/recall/F1 are not available. Dictionary coverage is not NER accuracy.

## Retrieval

The lexical TF-IDF baseline indexes 62 records across service, scheme, document/form, and official-source catalogues. Eight manually authored English query/record judgments yield Recall@1/3/5 and MRR of 1.000. The set is small, authored against known titles, and contains no Telugu or code-mixed judgments. It is a smoke evaluation only.

## Language detection and answer grounding

Language identification uses script and romanized-Telugu heuristics; no independent language-identification benchmark exists. Responses are templates/extracts of catalogue values and reviewed checklists, not generated answers. Source link presence does not prove an active service or current destination.
