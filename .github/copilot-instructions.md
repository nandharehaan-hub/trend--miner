# Trend Miner Repository Instructions

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Current Repository State

**CRITICAL**: This repository is currently in a minimal state with only a README.md file. There is no source code, build system, dependencies, or application logic yet.

## Working Effectively

### Repository Validation
- **Current validation command**: `cd /home/runner/work/trend--miner/trend--miner && ls -la`
  - **Expected output**: Should show only README.md and .git directory
  - **Time**: Instant
- **Verify README content**: `cat README.md`
  - **Expected content**: "# trend--miner\nMake money in your sleep"

### Repository Structure
Currently the repository contains:
```
.
├── .git/           # Git repository data
├── .github/        # GitHub configuration
│   └── copilot-instructions.md  # These instructions
└── README.md       # Basic project description
```

### Development Setup (Future)
When source code is added to this repository, common setup patterns to expect:

#### For Python Projects
If Python files are added:
- Look for `requirements.txt` or `pyproject.toml`
- Run `pip install -r requirements.txt` for dependencies
- Look for `pytest` or `unittest` for testing
- Common commands: `python -m pytest` (15-30 minutes typical, NEVER CANCEL, set timeout to 45+ minutes)

#### For Node.js Projects  
If `package.json` is added:
- Run `npm install` for dependencies (10-30 minutes typical, NEVER CANCEL, set timeout to 45+ minutes)
- Look for `npm test`, `npm run build`, `npm run dev` scripts
- Common build time: 20-45 minutes (NEVER CANCEL, set timeout to 60+ minutes)

#### For Docker Projects
If `Dockerfile` is added:
- Build with `docker build -t trend-miner .` (30-60 minutes typical, NEVER CANCEL, set timeout to 90+ minutes)
- Run with `docker run trend-miner`

### Current Available Commands

#### Safe Commands (Work Now)
- `pwd` - Show current directory
- `ls -la` - List repository contents
- `cat README.md` - View project description
- `git --no-pager status` - Check repository status
- `git --no-pager log --oneline -10` - View recent commits
- `find . -name "*.py" -o -name "*.js" -o -name "*.json"` - Search for future source files

#### Commands That Will Fail (Until Code Is Added)
- Any build commands (`npm install`, `pip install`, `make`, etc.)
- Any test commands (`npm test`, `pytest`, etc.)
- Any run commands (`npm start`, `python main.py`, etc.)

### Validation Scenarios

#### Current State Validation
Always verify the minimal repository state:
1. **Check repository contents**: `ls -la` should show README.md, .git, and .github directories
2. **Verify README**: `cat README.md` should contain project description
3. **Check for unexpected files**: `find . -type f ! -path './.git/*' ! -name 'README.md' ! -path './.github/*'` should return empty

#### Future Development Validation
When code is added, always:
1. **Check for build system**: Look for package.json, requirements.txt, Makefile, etc.
2. **Install dependencies**: Use appropriate package manager
3. **Build the project**: NEVER CANCEL builds, set timeouts to 60+ minutes minimum
4. **Run tests**: NEVER CANCEL test suites, set timeouts to 45+ minutes minimum
5. **Exercise functionality**: Test actual application features, not just startup/shutdown

### Time Expectations
- **File operations**: Instant
- **Git operations**: 1-5 seconds
- **Future builds**: 20-60 minutes (NEVER CANCEL, always set 90+ minute timeouts)
- **Future tests**: 5-45 minutes (NEVER CANCEL, always set 60+ minute timeouts)

### Common Issues and Solutions

#### Current State Issues
- **No source code**: This is expected. Repository is in initial state.
- **No build files**: This is expected. Wait for development to begin.
- **No tests**: This is expected in minimal repository state.

#### Future Development Issues
When development begins, watch for:
- **Missing dependencies**: Always run package manager install commands first
- **Build failures**: Check for platform-specific requirements (Windows vs Linux)
- **Test failures**: May indicate environmental setup issues
- **Long build times**: This is normal, NEVER CANCEL builds or tests

### Key Areas for Future Development
Based on the repository name "trend-miner" and description "Make money in your sleep":
- Likely to involve financial data analysis
- May include web scraping or API integration
- Could involve machine learning or data processing
- Watch for configuration files related to trading APIs or data sources

### Repository Metadata
- **Name**: trend--miner
- **Description**: Make money in your sleep
- **Current state**: Minimal/Initial
- **Primary files**: README.md only
- **Last validated**: When these instructions were created

### CRITICAL Reminders
- **NEVER CANCEL** any build or test commands when they are added
- **Always set timeouts** of 60+ minutes for builds, 45+ minutes for tests
- **Validate actual functionality** when code is added, not just startup/shutdown
- **Check these instructions first** before running exploratory commands
- **Document timing** for any new commands you discover work