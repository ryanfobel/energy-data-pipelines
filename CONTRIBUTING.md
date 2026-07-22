# Contributing to Energy Data Pipelines

Thank you for your interest in contributing! This guide will help you get started.

## Ways to Contribute

- 🐛 **Report bugs** - Found an issue? [Open a bug report](https://github.com/ryanfobel/energy-data-pipelines/issues/new?template=bug_report.md)
- ✨ **Suggest features** - Have an idea? [Request a feature](https://github.com/ryanfobel/energy-data-pipelines/issues/new?template=feature_request.md)
- 📖 **Improve documentation** - Fix typos, clarify instructions, add examples
- 🔧 **Fix bugs** - Pick an issue labeled `good first issue` or `bug`
- 🚀 **Add features** - Implement new data sources or transformations
- 💬 **Help others** - Answer questions in Discussions or Issues

## Development Setup

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/energy-data-pipelines.git
   cd energy-data-pipelines
   ```

2. **Install dependencies**
   ```bash
   pixi install
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make changes and test**
   ```bash
   pixi run generate-mock-data
   pixi run test-all
   ```

5. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Describe your changes clearly
   - Link related issues

## Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples:**
```
feat: add support for Sense energy monitor
fix: handle missing timestamps in Green Button data
docs: clarify InfluxDB export instructions
```

## Code Style

- **Python**: Follow PEP 8
- **SQL**: Use lowercase keywords, 2-space indentation
- **YAML**: 2-space indentation
- **Markdown**: Use ATX-style headers (#)

## Testing

Before submitting a PR:

```bash
# Run all tests
pixi run test-all

# Generate mock data
pixi run generate-mock-data

# Test pipelines
pixi run pipeline-all

# Test export
pixi run export-paimon
```

## Documentation

When adding features:
- Update relevant docs in `docs/`
- Add example queries if applicable
- Update `config.example.yml` if adding config options
- Add troubleshooting notes for common issues

## Adding a New Data Source

1. Create `pipelines/your_source/source.py`
2. Implement dlt source following existing patterns
3. Add staging model: `transform/models/staging/stg_your_source.sql`
4. Update `fct_electricity_consumption.sql` to UNION your data
5. Add tests: `scripts/test_your_source.py`
6. Document in `docs/SETUP.md` and `docs/USAGE.md`
7. Add example config: `docs/examples/your-source-only.yml`

See existing sources for reference:
- `pipelines/home_assistant/source.py`
- `transform/models/staging/stg_home_assistant_power.sql`

## Pull Request Guidelines

**Before submitting:**
- [ ] Tests pass (`pixi run test-all`)
- [ ] Documentation updated
- [ ] Commit messages follow format
- [ ] No merge conflicts with main
- [ ] PR description explains changes clearly

**After submitting:**
- Respond to review comments promptly
- Make requested changes
- Keep PR focused on one feature/fix

## Code Review Process

1. Maintainer reviews code within 1 week
2. Feedback provided as comments
3. Make requested changes
4. Maintainer merges when approved

## Questions?

- **Documentation**: Check [docs/FAQ.md](docs/FAQ.md)
- **Discussions**: [GitHub Discussions](https://github.com/ryanfobel/energy-data-pipelines/discussions)
- **Chat**: Join our community (link TBD)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for making energy data more accessible! 🌟
