"""Analysis — a pipeline of five stages run by two interchangeable strategies.

- :mod:`~taketwo.analysis.stages.understand` — recording → timeline + failure.
- :mod:`~taketwo.analysis.stages.reproduce` — timeline → reproduced run + evidence.
- :mod:`~taketwo.analysis.stages.repair` — evidence → localized cause + patch.
- :mod:`~taketwo.analysis.stages.prove` — patch → after clip + before/after proof.
- :mod:`~taketwo.analysis.stages.deliver` — artifacts → issue + draft PR.
- :mod:`~taketwo.analysis.pipeline` — the orchestrator (strategies + run machinery).

Side-effect free.
"""
