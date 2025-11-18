# SE333 Testing Agent  
An automated MCP (Model Context Protocol) testing agent designed to improve Java project test coverage using JaCoCo, automatically generate and fix tests, run static analysis, and manage Git workflows.

---

##  Overview

The **SE333 Testing Agent** is an automated system that:
- Finds untested Java source files
- Generates JUnit tests using a large language model
- Runs the full Maven test suite
- Analyzes test failures and automatically fixes them
- Computes JaCoCo coverage and identifies missing lines
- Performs static analysis (SpotBugs + code smells)
- Iteratively improves test coverage
- Automatically commits improvements at key thresholds
- Pushes changes and creates a pull request

This tool is built around MCP tools and fully automates software testing, static analysis, and Git operations.

---

#  MCP Tool / API Documentation

This agent uses a set of MCP tools to interact with the codebase, testing environment, and Git repo. Below is documentation for each tool used.

###  **Source Analysis Tools**
| Tool | Description |
|------|-------------|
| `find_java_source_files` | Scans the project to locate all Java source files. |
| `analyze_java_class` | Analyzes a specific Java class and its dependencies. |
| `read_test_file` | Reads test file content for inspection or modification. |

###  **Test Generation & Execution**
| Tool | Description |
|------|-------------|
| `generate_junit_tests` | Generates new JUnit test cases for uncovered classes. |
| `run_maven_test` | Executes the full Maven test suite. |
| `analyze_test_failures` | Extracts failing tests and explains the cause. |

###  **Coverage Tools**
| Tool | Description |
|------|-------------|
| `find_jacoco_path` | Locates the JaCoCo coverage file. |
| `total_coverage` | Computes overall line/branch coverage. |
| `missing_coverage` | Identifies uncovered methods/lines. |

###  **Static Analysis Tools**
| Tool | Description |
|------|-------------|
| `run_spotbugs_analysis` | Performs SpotBugs analysis and reports code issues. |
| `detect_code_smells` | Detects code smells or structural issues. |

###  **Git Automation Tools**
| Tool | Description |
|------|-------------|
| `git_status` | Shows the status of the working tree. |
| `git_add_all` | Stages all changes. |
| `git_commit` | Creates a commit with a custom message. |
| `git_push` | Pushes commits to the remote repository. |
| `git_pull_request` | Opens a pull request (if supported). |

---

# Installation & Configuration Guide

Follow the steps below to install, configure, and run the Testing Agent.

---

## 1️⃣ **Clone the Repository**
```bash
git clone https://github.com/kdang6/se333-testing-agent.git
cd se333-testing-agent
```

## 2️⃣ **Create a Python environment via MCP Server**
```bash
python -m venv venv
source venv/bin/activate      # macOS / Linux
.venv\Scripts\activate     # Windows PowerShell
```

## 3️⃣ **Make sure Maven is Installed**
The agent requires Maven 3+:
```
mvn -v
```

## 4️⃣ **Run the Agent**
Start your MCP client (ChatGPT, Claude Desktop, etc.) and load the testing agent.

The agent will automatically:
* Detect source files

* Generate missing tests

* Run Maven

* Improve coverage

* Commit & push results

---
## Troubleshooting & FAQ

**The agent pushed changes but GitHub didn’t show diffs**

Likely cause: Maven target/ directory was committed.
Solution:

Add .gitignore:
```
target/
*.class
```

