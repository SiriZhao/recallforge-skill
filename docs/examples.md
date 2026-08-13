# Examples

These examples use self-authored material and show expected workflow structure, not deterministic word-for-word model output.

## Probability: material to diagnosis

**Input:** a two-slide PPTX, one scan, and a short past-paper question covering conditional probability and independence.

**Material inspection:** slide titles/native formula are retained; the scan routes to host vision; every item receives a slide/page source anchor.

**Knowledge reconstruction:** conditional probability → independence → Bayes’ theorem, with the distinction between independence and mutual exclusivity flagged as diagnostic.

**Recall:** “Can mutually exclusive events with non-zero probability be independent? Explain from the definitions.”

**Learner answer:** “Yes, because they do not affect each other.”

**Diagnosis:** concept-condition confusion. Targeted repair compares `P(A∩B)=0` with `P(A∩B)=P(A)P(B)` and follows with one nearby question.

## Organic chemistry: visual evidence stays visual

**Input:** a slide containing a substrate, reaction arrow, intermediate, and products.

RecallForge keeps the reaction layout and substituent positions as visual evidence. OCR text such as `SN1` can support the interpretation but cannot replace the structure. An unclear bond or label is marked uncertain and linked to its slide.

## Botany: diagram-heavy material

**Input:** a self-authored leaf cross-section with labeled tissues.

RecallForge uses label placement and containment relationships to build a structure question, then asks the learner to identify which tissue performs a stated function. It does not infer taxonomy or species from appearance without source evidence.
