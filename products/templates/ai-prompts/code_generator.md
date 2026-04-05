# Code Generation Prompt Template

Structured prompt for generating production-quality code.

```
Generate code for the following task.

## Requirements
- Language: [LANGUAGE]
- Framework: [FRAMEWORK or 'none']
- Purpose: [DESCRIPTION]

## Code Standards
- Include type hints/annotations where the language supports them
- Add docstrings to all public functions
- Handle errors with try/except (do not silently swallow errors)
- Use meaningful variable names (no single letters except loop vars)
- Follow PEP 8 (Python) / standard style guide for the language

## Output Format
1. Brief description of the approach (2-3 sentences)
2. The complete, runnable code
3. Example usage showing expected input and output
4. Known limitations or edge cases

## Constraints
- Prefer standard library over third-party packages
- Code must be self-contained (no external config files required)
- Include a __main__ block for direct execution
```