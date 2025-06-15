# Contributing to PC Jewellers Enhanced Scraper

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- Chrome browser
- Basic knowledge of web scraping and Selenium

### Setting Up Development Environment

1. **Fork and Clone**

   ```bash
   git clone https://github.com/yourusername/pc-jewellers-scraper.git
   cd pc-jewellers-scraper
   ```

2. **Create Virtual Environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8  # Development tools
   ```

4. **Test Installation**
   ```bash
   python test_extraction.py
   ```

## 🎯 How to Contribute

### Types of Contributions

1. **Bug Reports** - Report issues with detailed reproduction steps
2. **Feature Requests** - Suggest new functionality
3. **Code Contributions** - Bug fixes, new features, optimizations
4. **Documentation** - Improve README, comments, examples
5. **Testing** - Add test cases, improve coverage

### Development Workflow

1. **Create Feature Branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**

   - Follow coding standards
   - Add tests for new features
   - Update documentation

3. **Test Your Changes**

   ```bash
   python test_extraction.py
   python quick_enhanced_test.py
   ```

4. **Commit Changes**

   ```bash
   git add .
   git commit -m "feat: add new metal type detection for titanium"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📋 Coding Standards

### Python Style Guide

- Follow PEP 8
- Use descriptive variable names
- Add docstrings to functions and classes
- Maximum line length: 100 characters

### Code Formatting

```bash
# Format code
black pc_jewellers_scraper_selenium.py

# Check style
flake8 pc_jewellers_scraper_selenium.py
```

### Example Function

```python
def extract_metal_type(self, container, product_name: str) -> str:
    """
    Extract metal type from product container or name.

    Args:
        container: BeautifulSoup container element
        product_name: Product name string

    Returns:
        str: Identified metal type or 'unknown'
    """
    try:
        # Implementation here
        return metal_type
    except Exception as e:
        self.logger.debug(f"Error extracting metal type: {str(e)}")
        return "unknown"
```

## 🧪 Testing Guidelines

### Test Structure

- Place tests in `test_*.py` files
- Use descriptive test names
- Test both success and failure cases

### Running Tests

```bash
# Run specific test
python test_extraction.py

# Run all tests
python -m pytest tests/ -v
```

### Adding New Tests

```python
def test_metal_type_extraction():
    """Test metal type extraction from various product names."""
    scraper = PCJewellersScraper()

    test_cases = [
        ("Gold Ring 18K", "gold"),
        ("Sterling Silver Bracelet", "silver"),
        ("Platinum Necklace", "platinum"),
    ]

    for product_name, expected_metal in test_cases:
        result = scraper.identify_metal_from_text(product_name.lower())
        assert result == expected_metal, f"Expected {expected_metal}, got {result}"
```

## 📚 Documentation Guidelines

### Code Documentation

- Add docstrings to all public functions
- Include parameter types and descriptions
- Provide usage examples

### README Updates

- Keep README.md current with new features
- Add examples for new functionality
- Update installation instructions if needed

## 🐛 Bug Reports

### Bug Report Template

```markdown
**Bug Description**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:

1. Run command '...'
2. Navigate to '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Screenshots/Logs**
If applicable, add screenshots or log outputs.

**Environment:**

- OS: [e.g. Windows 10]
- Python Version: [e.g. 3.9]
- Chrome Version: [e.g. 119.0]
```

## 💡 Feature Requests

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Explain why this feature would be useful.

**Proposed Implementation**
If you have ideas on how to implement this, please share.

**Alternatives Considered**
Other solutions you've considered.
```

## 🔄 Pull Request Process

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Tested locally
- [ ] Added/updated tests
- [ ] All tests pass

## Screenshots (if applicable)

Add screenshots to help explain your changes.
```

## 🏷️ Commit Message Guidelines

### Format

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(scraper): add titanium metal type detection
fix(analyzer): handle empty price data gracefully
docs(readme): update installation instructions
test(extraction): add weight extraction test cases
```

## 🔒 Security Guidelines

### Reporting Security Issues

- Do not open public issues for security vulnerabilities
- Email security concerns to [your-email@example.com]
- Include detailed reproduction steps

### Security Best Practices

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Validate all user inputs
- Follow rate limiting guidelines

## 📦 Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):

- MAJOR.MINOR.PATCH (e.g., 1.2.3)
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Creating Releases

1. Update version in `setup.py` or `__version__.py`
2. Update CHANGELOG.md
3. Create GitHub release with release notes
4. Tag the release: `git tag v1.2.3`

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help others learn and grow

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Requests**: Code contributions

## 📞 Getting Help

### Before Asking for Help

1. Check existing issues and discussions
2. Read the documentation
3. Try the troubleshooting section
4. Search for similar problems online

### How to Ask for Help

1. Use descriptive titles
2. Provide context and background
3. Include error messages and logs
4. Share your environment details
5. Describe what you've already tried

## 🎉 Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- GitHub contributors graph

Thank you for contributing to the PC Jewellers Enhanced Scraper! 🚀
