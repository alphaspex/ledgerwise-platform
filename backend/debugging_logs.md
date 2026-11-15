<!-- Inputs: actual backend debugging events with file path, bug explanation (maximum 40 words), attempted fix (maximum 50 words), and yes/no outcome. -->
<!-- Outputs: chronological debugging entries in the required // filename — bug — fix — worked format. -->
<!-- Explanation: Records only debugging work; read this file before debugging any backend file. -->
# Backend debugging log

No debugging events recorded yet.
// orchestrator.py — Bug: draft planning could enqueue duplicate work; search lacked active-run selection and exclusions; source URL decoding and claimed-job selection were inconsistent. Fix tried: correcting queue guards, passing current run and exclusions to search, and fixing the result/claim lifecycle. Worked: no.
