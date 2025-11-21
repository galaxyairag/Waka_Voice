# CLAUDE.md - AI Assistant Guide for Waka_Voice

This document provides context and guidelines for AI assistants working on the Waka_Voice project.

## Project Overview

**Project Name:** Waka_Voice
**Status:** Initial development phase
**Repository:** galaxyairag/Waka_Voice

Waka_Voice is a new project currently in its initialization phase. The codebase structure and technology stack are yet to be established.

## Current Repository Structure

```
Waka_Voice/
├── CLAUDE.md          # AI assistant guidelines (this file)
├── README.md          # Project documentation
└── .git/              # Git repository metadata
```

## Development Guidelines

### Git Workflow

- **Main Development:** Work on feature branches prefixed with `claude/`
- **Commit Messages:** Use clear, descriptive commit messages
- **Push Command:** Always use `git push -u origin <branch-name>`

### Branch Naming Convention

```
claude/<description>-<session-id>
```

### Commit Message Format

```
<type>: <short description>

[optional body with more details]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

## Code Conventions

### General Principles

1. **Readability:** Write clear, self-documenting code
2. **Modularity:** Keep functions and modules focused on single responsibilities
3. **Error Handling:** Always handle errors gracefully with meaningful messages
4. **Documentation:** Document public APIs and complex logic
5. **Security:** Never commit secrets, credentials, or sensitive data

### File Organization

When the project structure is established, follow these conventions:

```
src/           # Source code
tests/         # Test files
docs/          # Documentation
config/        # Configuration files
scripts/       # Build/utility scripts
```

## Commands Reference

### Git Commands

```bash
# Check status
git status

# Stage changes
git add <files>

# Commit changes
git commit -m "type: description"

# Push to remote
git push -u origin <branch-name>

# Pull latest changes
git pull origin <branch-name>
```

## AI Assistant Instructions

### When Working on This Project

1. **Explore First:** Always understand the current state before making changes
2. **Plan Changes:** Use TodoWrite to track multi-step tasks
3. **Test Changes:** Verify changes work before committing
4. **Document:** Update relevant documentation when making significant changes
5. **Commit Often:** Make small, focused commits rather than large monolithic ones

### What to Avoid

- Do not commit sensitive information (API keys, passwords, tokens)
- Do not force push to shared branches
- Do not modify files outside the project scope
- Do not introduce dependencies without clear justification

### Code Quality Checklist

Before committing, verify:
- [ ] Code compiles/runs without errors
- [ ] No security vulnerabilities introduced
- [ ] Changes are properly documented
- [ ] Commit message follows convention

## Project Roadmap

This section will be updated as the project develops:

- [ ] Define project scope and requirements
- [ ] Choose technology stack
- [ ] Set up project structure
- [ ] Implement core functionality
- [ ] Add testing framework
- [ ] Configure CI/CD pipeline
- [ ] Write comprehensive documentation

## Contact

**Maintainer:** galaxyairag
**Email:** nabil@galaxyai.digital

---

*Last updated: 2025-11-21*
