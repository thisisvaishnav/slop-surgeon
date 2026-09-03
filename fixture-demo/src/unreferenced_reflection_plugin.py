"""
Plugin loaded at runtime via config/eval.
Static scanners will think it is dead, but tests will fail if it is excised!
"""

def dynamic_feature():
    return "critical_dynamic_result"
