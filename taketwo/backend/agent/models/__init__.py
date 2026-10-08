"""Model construction â€” a generic openjiuwen model builder.

Import from this package (the folder) rather than its submodules.
"""

from taketwo.backend.agent.models.builder import build_model
from taketwo.backend.agent.models.params import ModelParams

__all__ = ["ModelParams", "build_model"]
