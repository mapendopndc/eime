---
applyTo: '**'
---

# EIME Development Guidelines

## Core Principles

### Simplicity First
- Keep implementations simple and straightforward
- Avoid over-engineering solutions
- Favor clarity over cleverness
- Don't add abstractions unless they provide clear value

### Engineering Formula Preservation
- **Critical**: Preserve the format and readability of engineering formulas
- Formulas must remain human-readable and verifiable by engineers
- Keep formula functions simple, direct, and mathematically transparent
- Avoid wrapping formulas in excessive abstractions or boilerplate
- Document formulas concisely - focus on what's needed to understand and verify them

### Code Hygiene
- **Always delete unused code** - no keeping "just in case"
- No backwards compatibility requirements - refactor freely
- Remove dead imports, commented-out code, and obsolete functions immediately
- Keep the codebase lean and focused

### Documentation
- Be concise - avoid verbose documentation
- Document *why* when it's not obvious, not *what* when code is clear
- Focus on engineering context and formula references, not restating the code
- Examples over lengthy explanations

## Python Best Practices

### Modern Python
- Use Python 3.10+ features (type hints, pattern matching, etc.)
- Type hints on all public APIs
- Follow PEP 8 style guide
- Maximum line length: 100 characters

### Object-Oriented Design
- Single Responsibility Principle
- Composition over inheritance when practical
- Keep classes focused and cohesive
- Avoid deep inheritance hierarchies

### Package Management
- **Use UV exclusively** for package management
- Define dependencies in `pyproject.toml`
- No requirements.txt unless absolutely necessary
- Keep dependencies minimal

## Engineering-Specific Guidelines

### Formula Design
```python
# Good: Simple, transparent, verifiable
def beam_deflection(L: float, E: float, I: float, w: float) -> float:
    """Calculate maximum deflection of simply supported beam with uniform load.
    
    Reference: CSA S16-19 Clause X.X
    """
    return (5 * w * L**4) / (384 * E * I)

# Bad: Over-abstracted, hard to verify
class BeamDeflectionCalculator:
    def __init__(self, config: BeamConfig):
        self.validator = DeflectionValidator(config)
        self.processor = LoadProcessor()
    # ... 50 more lines
```

### Batch Calculations
- Support numpy arrays for batch processing
- Keep formula logic identical for scalar and array inputs
- Let numpy handle broadcasting naturally

## What to Avoid

- ❌ Over-abstraction and excessive class hierarchies
- ❌ Verbose documentation that restates obvious code
- ❌ Keeping unused or deprecated code
- ❌ Complex inheritance when composition works
- ❌ Adding features "for future use"
- ❌ Backwards compatibility concerns
- ❌ Magic methods and operator overloading without clear benefit

## When Making Changes

1. **Delete first**: Remove unused code before adding new
2. **Simplify**: Look for ways to reduce complexity
3. **Verify formulas**: Ensure engineering calculations remain transparent
4. **Test**: Write tests, but keep them simple too
5. **Document briefly**: Add only necessary context

---

*Remember: This is engineering software. Formulas must be verifiable by humans. Keep it simple, keep it clean, keep it focused.*
