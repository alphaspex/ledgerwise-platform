<!-- Inputs: actual backend debugging events with file path, bug explanation (maximum 40 words), attempted fix (maximum 50 words), and yes/no outcome. -->
<!-- Outputs: chronological debugging entries in the required // filename — bug — fix — worked format. -->
<!-- Explanation: Records only debugging work; read this file before debugging any backend file. -->
# Backend debugging log

// orchestrator.py — Bug: draft planning could enqueue duplicate work; search lacked active-run selection and exclusions; source URL decoding and claimed-job selection were inconsistent. Fix tried: correcting queue guards, passing current run and exclusions to search, and fixing the result/claim lifecycle. Worked: no.
// api.py — Bug: research start violated the single-writer queue rule; human reply selected the wrong row after queue insertion; invitation audit used the password-code ID; code expiry handling could compare naive and aware datetimes. Fix tried: moving queue writes to the orchestrator, using RETURNING for message rows, selecting user IDs by email, and normalizing expiry timestamps. Worked: no.
// integrations.py — Bug: Apollo candidates without an explicit current-employer domain were treated as matching the target company, and unclassified titles could proceed to enrichment. Fix tried: require a returned employer domain match and an approved role before People Match. Worked: no.
