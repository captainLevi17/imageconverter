# Contributing to Image Master

First off, thank you for considering contributing to Image Master! It's people like you that make Image Master such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

- **Ensure the bug was not already reported** by searching on GitHub under [Issues](https://github.com/yourusername/imageconverter/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/yourusername/imageconverter/issues/new). Be sure to include:
  - A clear and descriptive title
  - Steps to reproduce the issue
  - Expected vs. actual behavior
  - Screenshots if applicable
  - Your operating system and Python version

### Suggesting Enhancements

- Use GitHub Issues to submit your enhancement suggestions.
- Clearly describe the feature and why you believe it would be useful.
- Include any relevant screenshots or mockups.

### Your First Code Contribution

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/imageconverter.git
   cd imageconverter
   git remote add upstream https://github.com/original_owner/imageconverter.git
   ```
3. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following the coding standards.
5. **Test your changes** thoroughly.
6. **Commit your changes** with a descriptive message:
   ```bash
   git commit -m "Add: Your feature description"
   ```
7. **Push to your fork** and create a pull request.

## Development Setup

1. Set up your development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide.
- Use type hints for better code clarity.
- Write docstrings for all public functions and classes.
- Keep functions small and focused on a single task.
- Write tests for new functionality.

## Testing

Run the test suite with:
```bash
pytest
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, including new environment variables, exposed ports, useful file locations, and container parameters.
3. Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent.
4. The PR will be reviewed by the maintainers and may require changes before being merged.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
