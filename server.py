from fastmcp import FastMCP
import subprocess
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import json
from datetime import datetime

mcp = FastMCP("Testing Agent")

MAVEN_PROJECT_PATH = "./codebase" 

## Phase 2 Tools

@mcp.tool()
def find_java_source_files() -> dict:
    """
    Find all Java source files in the Maven project that need testing.
    """

    try:
        src_path = Path(MAVEN_PROJECT_PATH) / "src/main/java"
        
        if not src_path.exists():
            return {"error": f"Source path not found: {src_path}"}
        
        java_files = []
        for java_file in src_path.rglob("*.java"):
            relative_path = java_file.relative_to(Path(MAVEN_PROJECT_PATH))
            java_files.append({
                "path": str(relative_path),
                "absolute_path": str(java_file),
                "name": java_file.name
            })
        
        return {
            "total_files": len(java_files),
            "files": java_files,
            "source_directory": str(src_path)
        }
    
    except Exception as e:
        return {"error": f"Failed to find source files: {str(e)}"}


@mcp.tool()
def analyze_java_class(file_path: str) -> dict:
    """
    Analyze a Java class and extract its structure for test generation.
    """

    full_path = Path(MAVEN_PROJECT_PATH) / file_path
    
    if not full_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract package
        package_match = re.search(r'package\s+([\w.]+);', content)
        package = package_match.group(1) if package_match else ""
        
        # Extract class name
        class_match = re.search(r'public\s+class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else ""
        
        # Extract imports
        imports = re.findall(r'import\s+([\w.]+);', content)
        
        # Extract methods with more detail
        method_pattern = r'(public|private|protected|)\s+(static\s+)?(\w+)\s+(\w+)\s*\((.*?)\)\s*(?:throws\s+[\w\s,]+)?\s*\{'
        methods = []
        
        for match in re.finditer(method_pattern, content):
            visibility = match.group(1) or "default"
            is_static = match.group(2) is not None
            return_type = match.group(3)
            method_name = match.group(4)
            params = match.group(5).strip()
            
            # Skip constructors
            if method_name == class_name:
                continue
            
            # Parse parameters
            param_list = []
            if params:
                for param in params.split(','):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_list.append({
                                "type": parts[-2],
                                "name": parts[-1]
                            })
            
            methods.append({
                "visibility": visibility,
                "static": is_static,
                "return_type": return_type,
                "name": method_name,
                "parameters": param_list,
                "param_string": params
            })
        
        return {
            "file_path": file_path,
            "package": package,
            "class_name": class_name,
            "imports": imports,
            "methods": methods,
            "method_count": len(methods)
        }
    
    except Exception as e:
        return {"error": f"Failed to analyze class: {str(e)}"}


@mcp.tool()
def generate_junit_tests(java_file_path: str) -> dict:
    """
    Generate JUnit test file for a Java class.
    
    Args:
        java_file_path: Path to Java source file (e.g., "src/main/java/com/example/Calculator.java")
    """
    # Step 1: Analyze the class
    class_info = analyze_java_class(java_file_path)
    
    if "error" in class_info:
        return class_info
    
    package = class_info.get("package", "")
    class_name = class_info.get("class_name", "")
    methods = class_info.get("methods", [])
    
    if not class_name:
        return {"error": "No class name found in file"}
    
    test_class_name = f"{class_name}Test"
    
    # Step 2: Generate simple, working test code
    test_code = f"""package {package};

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.BeforeEach;
import static org.junit.jupiter.api.Assertions.*;

public class {test_class_name} {{
    
    private {class_name} instance;
    
    @BeforeEach
    public void setUp() {{
        instance = new {class_name}();
    }}
"""
    
    # Generate one simple test per method
    for method in methods:
        method_name = method['name']
        return_type = method['return_type']
        params = method.get('parameters', [])
        
        param_calls = []
        for param in params:
            param_type = param['type']
            if 'int' in param_type.lower():
                param_calls.append('1')
            elif 'double' in param_type.lower() or 'float' in param_type.lower():
                param_calls.append('1.0')
            elif 'boolean' in param_type.lower():
                param_calls.append('true')
            elif 'String' in param_type:
                param_calls.append('"test"')
            elif 'char' in param_type.lower():
                param_calls.append("'a'")
            else:
                param_calls.append('null')
        
        param_call = ', '.join(param_calls)
        
        test_code += f"""
    @Test
    public void test{method_name.capitalize()}() {{
        // Basic test for {method_name}
        """
        
        if return_type == 'void':
            test_code += f"""instance.{method_name}({param_call});
        // If no exception thrown, test passes
        assertTrue(true);
    }}
"""
        else:
            test_code += f"""{return_type} result = instance.{method_name}({param_call});
        assertNotNull(result);
    }}
"""
    
    test_code += "}\n"
    
    # Step 4: Write the test file
    test_path = f"src/test/java/{package.replace('.', '/')}/{test_class_name}.java"
    full_output_path = Path(MAVEN_PROJECT_PATH) / test_path
    
    # Create directory if needed
    full_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        return {
            "success": True,
            "test_file": test_path,
            "test_class": test_class_name,
            "methods_tested": len(methods),
            "message": f"Generated {len(methods)} tests for {class_name}"
        }
    
    except Exception as e:
        return {"error": f"Failed to write test file: {str(e)}"}


@mcp.tool()
def generate_all_missing_tests() -> dict:
    """
    Find all Java classes without tests and generate tests for them automatically.
    """

    # Find all source files
    source_result = find_java_source_files()
    
    if "error" in source_result:
        return source_result
    
    java_files = source_result.get("files", [])
    results = {
        "total_files": len(java_files),
        "tests_generated": 0,
        "tests_skipped": 0,
        "errors": [],
        "generated_files": []
    }
    
    for file_info in java_files:
        file_path = file_info["path"]
        
        # Check if test already exists
        # Convert src/main/java/com/example/Foo.java -> src/test/java/com/example/FooTest.java
        test_path = file_path.replace("src/main/", "src/test/").replace(".java", "Test.java")
        full_test_path = Path(MAVEN_PROJECT_PATH) / test_path
        
        if full_test_path.exists():
            results["tests_skipped"] += 1
            continue
        
        # Generate test
        result = generate_junit_tests(file_path)
        
        if "error" in result:
            results["errors"].append({
                "file": file_path,
                "error": result["error"]
            })
        elif result.get("success"):
            results["tests_generated"] += 1
            results["generated_files"].append(result.get("test_file"))
    
    results["message"] = f"Generated {results['tests_generated']} new test files, skipped {results['tests_skipped']} existing tests"
    
    return results


@mcp.tool()
def run_maven_test(project_path: str) -> dict:
    """Run Maven tests, ignoring failures to generate coverage"""
    result = subprocess.run(
        ["mvn", "clean", "test", "-Dmaven.test.failure.ignore=true"],
        cwd=project_path,
        capture_output=True,
        text=True,
        timeout=600
    )
    return {
        "success": True,  # Always return success since we ignore failures
        "output": result.stdout,
        "errors": result.stderr,
        "return_code": result.returncode
    }


@mcp.tool()
def find_jacoco_path() -> dict:
    """
    Find the JaCoCo XML report path after running tests.
    
    Returns:
        Dictionary with JaCoCo report path and status
    """
    try:
        # Standard JaCoCo path
        jacoco_xml = Path(MAVEN_PROJECT_PATH) / "target/site/jacoco/jacoco.xml"
        
        if jacoco_xml.exists():
            return {
                "found": True,
                "path": str(jacoco_xml),
                "relative_path": "target/site/jacoco/jacoco.xml",
                "size_bytes": jacoco_xml.stat().st_size
            }
        else:
            target_dir = Path(MAVEN_PROJECT_PATH) / "target"
            found_files = list(target_dir.rglob("jacoco.xml")) if target_dir.exists() else []
            
            if found_files:
                return {
                    "found": True,
                    "path": str(found_files[0]),
                    "relative_path": str(found_files[0].relative_to(Path(MAVEN_PROJECT_PATH)))
                }
            else:
                return {
                    "found": False,
                    "error": "JaCoCo report not found. Ensure JaCoCo plugin is configured in pom.xml and 'mvn test' has been run.",
                    "expected_path": str(jacoco_xml)
                }
    
    except Exception as e:
        return {"error": f"Failed to find JaCoCo path: {str(e)}"}


@mcp.tool()
def missing_coverage(jacoco_path: str) -> dict:
    """
    Parse JaCoCo XML report to identify missing coverage.

    """

    try:
        if not Path(jacoco_path).exists():
            return {"error": f"JaCoCo file not found: {jacoco_path}"}
        
        tree = ET.parse(jacoco_path)
        root = tree.getroot()
        
        missing_data = {
            "uncovered_classes": [],
            "uncovered_methods": [],
            "partially_covered_classes": [],
            "total_uncovered_lines": 0,
            "recommendations": []
        }
        
        for package in root.findall('.//package'):
            package_name = package.get('name', '').replace('/', '.')
            
            for class_elem in package.findall('.//class'):
                class_name = class_elem.get('name', '').replace('/', '.').split('$')[0]
                source_file = class_elem.get('sourcefilename', '')
                
                class_data = {
                    "package": package_name,
                    "class": class_name,
                    "source_file": source_file,
                    "uncovered_methods": [],
                    "total_lines": 0,
                    "covered_lines": 0,
                    "missed_lines": 0
                }

                for method in class_elem.findall('.//method'):
                    method_name = method.get('name')
                    method_desc = method.get('desc', '')

                    if method_name in ['<init>', '<clinit>']:
                        continue
                    
                    method_coverage = {
                        "name": method_name,
                        "descriptor": method_desc,
                        "missed_instructions": 0,
                        "covered_instructions": 0,
                        "missed_lines": 0,
                        "covered_lines": 0
                    }
                    
                    for counter in method.findall('.//counter'):
                        counter_type = counter.get('type')
                        missed = int(counter.get('missed', 0))
                        covered = int(counter.get('covered', 0))
                        
                        if counter_type == 'INSTRUCTION':
                            method_coverage['missed_instructions'] = missed
                            method_coverage['covered_instructions'] = covered
                        elif counter_type == 'LINE':
                            method_coverage['missed_lines'] = missed
                            method_coverage['covered_lines'] = covered
                    
                    total_lines = method_coverage['missed_lines'] + method_coverage['covered_lines']
                    
                    if total_lines > 0:
                        coverage_pct = (method_coverage['covered_lines'] / total_lines) * 100
                        method_coverage['coverage_percent'] = round(coverage_pct, 2)
                        
                        # Track uncovered methods
                        if coverage_pct == 0:
                            class_data['uncovered_methods'].append(method_coverage)
                        elif coverage_pct < 100:
                            method_coverage['status'] = 'partially_covered'
                            class_data['uncovered_methods'].append(method_coverage)
                    
                    class_data['total_lines'] += method_coverage['covered_lines'] + method_coverage['missed_lines']
                    class_data['covered_lines'] += method_coverage['covered_lines']
                    class_data['missed_lines'] += method_coverage['missed_lines']
                
                # Categorize classes
                if class_data['total_lines'] > 0:
                    class_coverage_pct = (class_data['covered_lines'] / class_data['total_lines']) * 100
                    class_data['coverage_percent'] = round(class_coverage_pct, 2)
                    
                    if class_coverage_pct == 0:
                        missing_data['uncovered_classes'].append(class_data)
                    elif class_coverage_pct < 100 and class_data['uncovered_methods']:
                        missing_data['partially_covered_classes'].append(class_data)
                    
                    missing_data['total_uncovered_lines'] += class_data['missed_lines']
        
        # Generate recommendations
        if missing_data['uncovered_classes']:
            missing_data['recommendations'].append(
                f"PRIORITY: {len(missing_data['uncovered_classes'])} classes have 0% coverage. Generate tests for these first."
            )
        
        if missing_data['partially_covered_classes']:
            missing_data['recommendations'].append(
                f"Found {len(missing_data['partially_covered_classes'])} partially covered classes. "
                f"Add tests for uncovered methods."
            )
        
        if missing_data['total_uncovered_lines'] > 0:
            missing_data['recommendations'].append(
                f"Total uncovered lines: {missing_data['total_uncovered_lines']}. "
                f"Focus on critical business logic first."
            )
        
        return missing_data
    
    except Exception as e:
        return {"error": f"Failed to parse JaCoCo report: {str(e)}"}


@mcp.tool()
def total_coverage(jacoco_path: str) -> dict:
    """
    Calculate total code coverage statistics from JaCoCo report.
    """

    try:
        if not Path(jacoco_path).exists():
            return {"error": f"JaCoCo file not found: {jacoco_path}"}
        
        tree = ET.parse(jacoco_path)
        root = tree.getroot()
        
        coverage_stats = {
            "instruction_coverage": {},
            "branch_coverage": {},
            "line_coverage": {},
            "method_coverage": {},
            "class_coverage": {}
        }
        
        # Parse counters at report level
        for counter in root.findall('./counter'):
            counter_type = counter.get('type')
            missed = int(counter.get('missed', 0))
            covered = int(counter.get('covered', 0))
            total = missed + covered
            
            if total > 0:
                percentage = (covered / total) * 100
                
                coverage_data = {
                    "missed": missed,
                    "covered": covered,
                    "total": total,
                    "percentage": round(percentage, 2)
                }
                
                if counter_type == 'INSTRUCTION':
                    coverage_stats['instruction_coverage'] = coverage_data
                elif counter_type == 'BRANCH':
                    coverage_stats['branch_coverage'] = coverage_data
                elif counter_type == 'LINE':
                    coverage_stats['line_coverage'] = coverage_data
                elif counter_type == 'METHOD':
                    coverage_stats['method_coverage'] = coverage_data
                elif counter_type == 'CLASS':
                    coverage_stats['class_coverage'] = coverage_data
        
        # Overall assessment
        line_cov = coverage_stats.get('line_coverage', {})
        if line_cov:
            pct = line_cov.get('percentage', 0)
            
            if pct >= 80:
                coverage_stats['assessment'] = f"EXCELLENT: {pct}% line coverage"
            elif pct >= 60:
                coverage_stats['assessment'] = f"GOOD: {pct}% line coverage - aim for 80%"
            elif pct >= 40:
                coverage_stats['assessment'] = f"FAIR: {pct}% line coverage - needs improvement"
            else:
                coverage_stats['assessment'] = f"POOR: {pct}% line coverage - critical gap"
        
        return coverage_stats
    
    except Exception as e:
        return {"error": f"Failed to calculate coverage: {str(e)}"}


@mcp.tool()
def analyze_test_failures() -> dict:
    """
    Analyze test failure reports to identify what went wrong.
    """

    try:
        surefire_reports = Path(MAVEN_PROJECT_PATH) / "target/surefire-reports"
        
        if not surefire_reports.exists():
            return {"error": "No surefire reports found. Run tests first."}
        
        failures = []
        errors = []
        
        # Parse XML test reports
        for xml_file in surefire_reports.glob("TEST-*.xml"):
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                for testcase in root.findall('.//testcase'):
                    class_name = testcase.get('classname')
                    test_name = testcase.get('name')
                    
                    # Check for failures
                    failure = testcase.find('failure')
                    if failure is not None:
                        failures.append({
                            "class": class_name,
                            "test": test_name,
                            "type": failure.get('type'),
                            "message": failure.get('message'),
                            "detail": failure.text[:500] if failure.text else ""
                        })
                    
                    # Check for errors
                    error = testcase.find('error')
                    if error is not None:
                        errors.append({
                            "class": class_name,
                            "test": test_name,
                            "type": error.get('type'),
                            "message": error.get('message'),
                            "detail": error.text[:500] if error.text else ""
                        })
            
            except Exception as e:
                continue
        
        return {
            "total_failures": len(failures),
            "total_errors": len(errors),
            "failures": failures[:10],  # First 10 failures
            "errors": errors[:10],  # First 10 errors
            "recommendations": [
                "Fix compilation errors first (check errors list)",
                "Then fix assertion failures (check failures list)",
                "Common issues: NullPointerException, AssertionError, IllegalArgumentException"
            ]
        }
    
    except Exception as e:
        return {"error": f"Failed to analyze test failures: {str(e)}"}


@mcp.tool()
def read_test_file(test_file_path: str) -> dict:
    """
    Reads a test file.
    """
    full_path = Path(MAVEN_PROJECT_PATH) / test_file_path
    
    if not full_path.exists():
        return {"error": f"Test file not found: {test_file_path}"}
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "path": test_file_path,
            "content": content,
            "line_count": len(content.split('\n'))
        }
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}


# Phase 3: Git Integration/Tools
@mcp.tool()
def git_status(repo_path: str) -> dict:
    """
    Get Git repository status.
    
    Returns:
        Dictionary with status information including:
        - clean: Whether working tree is clean
        - staged_files: List of staged files
        - unstaged_files: List of modified but unstaged files
        - untracked_files: List of untracked files
        - conflicts: List of files with merge conflicts
        - current_branch: Name of current branch
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip()
        
        # Get detailed status
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        
        staged_files = []
        unstaged_files = []
        untracked_files = []
        conflicts = []
        
        for line in status_lines:
            if not line:
                continue
            
            status_code = line[:2]
            filename = line[3:]
            
            # Staged files (first character is not space or ?)
            if status_code[0] not in [' ', '?']:
                staged_files.append(filename)
            
            # Unstaged files (second character is M, D, etc.)
            if status_code[1] in ['M', 'D', 'A']:
                unstaged_files.append(filename)
            
            # Untracked files
            if status_code == '??':
                untracked_files.append(filename)
            
            # Conflicts (both modified or unmerged)
            if status_code in ['UU', 'AA', 'DD', 'AU', 'UA', 'DU', 'UD']:
                conflicts.append(filename)
        
        is_clean = len(status_lines) == 0 or (len(status_lines) == 1 and not status_lines[0])
        
        return {
            "success": True,
            "clean": is_clean,
            "current_branch": current_branch,
            "staged_files": staged_files,
            "unstaged_files": unstaged_files,
            "untracked_files": untracked_files,
            "conflicts": conflicts,
            "total_changes": len(staged_files) + len(unstaged_files) + len(untracked_files)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def git_add_all(repo_path: str, exclude_patterns: list = None) -> dict:
    """
    Stage all changes with intelligent filtering to exclude build artifacts.
    
    Returns:
        Dictionary with staging results
    """
    try:
        # Default exclude patterns for build artifacts and temporary files
        default_excludes = [
            "target/",
            "*.class",
            "*.jar",
            "*.war",
            "*.ear",
            ".DS_Store",
            "*.swp",
            "*.swo",
            "*~",
            ".venv/",
            "__pycache__/",
            "*.pyc",
            "node_modules/",
            ".idea/",
            "*.iml",
            ".vscode/settings.json"
        ]
        
        # Combine with user-provided excludes
        if exclude_patterns:
            default_excludes.extend(exclude_patterns)
        
        # First, add all files
        add_result = subprocess.run(
            ["git", "add", "-A"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if add_result.returncode != 0:
            return {
                "success": False,
                "error": add_result.stderr
            }
        
        # Then unstage files matching exclude patterns
        for pattern in default_excludes:
            subprocess.run(
                ["git", "reset", "HEAD", pattern],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
        
        # Get what was actually staged
        status_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        staged_files = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        
        return {
            "success": True,
            "staged_files": staged_files,
            "count": len(staged_files),
            "message": f"Successfully staged {len(staged_files)} file(s)"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def git_commit(repo_path: str, message: str, coverage_stats: dict = None) -> dict:
    """
    Create a commit with standardized message format.
    
    Args:
        repo_path: Path to the Git repository
        message: Commit message
        coverage_stats: Optional dictionary with coverage statistics to include
                       Expected format: {"line_coverage": 85.5, "branch_coverage": 78.2}
    
    Returns:
        Dictionary with commit results
    """
    try:
        # Build commit message with coverage stats if provided
        full_message = message
        
        if coverage_stats:
            coverage_info = "\n\n[Coverage Stats]"
            if "line_coverage" in coverage_stats:
                coverage_info += f"\nLine Coverage: {coverage_stats['line_coverage']:.2f}%"
            if "branch_coverage" in coverage_stats:
                coverage_info += f"\nBranch Coverage: {coverage_stats['branch_coverage']:.2f}%"
            if "method_coverage" in coverage_stats:
                coverage_info += f"\nMethod Coverage: {coverage_stats['method_coverage']:.2f}%"
            if "test_count" in coverage_stats:
                coverage_info += f"\nTests: {coverage_stats['test_count']}"
            
            full_message += coverage_info
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message += f"\n\nCommitted: {timestamp}"
        
        # Create commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", full_message],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode != 0:
            # Check if it's because there's nothing to commit
            if "nothing to commit" in commit_result.stdout:
                return {
                    "success": True,
                    "message": "Nothing to commit - working tree clean",
                    "commit_hash": None
                }
            return {
                "success": False,
                "error": commit_result.stderr
            }
        
        # Get commit hash
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        commit_hash = hash_result.stdout.strip()
        
        return {
            "success": True,
            "commit_hash": commit_hash,
            "message": f"Successfully committed as {commit_hash[:7]}",
            "full_output": commit_result.stdout
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def git_push(repo_path: str, remote: str = "origin", branch: str = None) -> dict:
    """
    Push commits to remote repository.
    
    Args:
        repo_path: Path to the Git repository
        remote: Remote name (default: "origin")
        branch: Branch name (if None, pushes current branch)
    
    Returns:
        Dictionary with push results
    """
    try:
        # Get current branch if not specified
        if branch is None:
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            branch = branch_result.stdout.strip()
        
        # Check if remote exists
        remote_check = subprocess.run(
            ["git", "remote", "get-url", remote],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if remote_check.returncode != 0:
            return {
                "success": False,
                "error": f"Remote '{remote}' does not exist"
            }
        
        remote_url = remote_check.stdout.strip()
        
        # Push with set-upstream
        push_result = subprocess.run(
            ["git", "push", "--set-upstream", remote, branch],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            return {
                "success": False,
                "error": push_result.stderr,
                "hint": "Check if you have proper authentication credentials configured"
            }
        
        return {
            "success": True,
            "remote": remote,
            "branch": branch,
            "remote_url": remote_url,
            "message": f"Successfully pushed to {remote}/{branch}",
            "output": push_result.stderr  # Git push outputs to stderr
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def git_pull_request(
    repo_path: str,
    base: str = "main",
    title: str = "",
    body: str = "",
    coverage_improvement: dict = None,
    bug_fixes: list = None
) -> dict:
    """
    Create a pull request using GitHub CLI (gh).
    
    Args:
        repo_path: Path to the Git repository
        base: Base branch for PR (default: "main")
        title: PR title
        body: PR description
        coverage_improvement: Optional dict with before/after coverage stats
        bug_fixes: Optional list of bug descriptions that were fixed
    
    Returns:
        Dictionary with PR creation results including URL
    """
    try:
        # Check if gh CLI is installed
        gh_check = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True
        )
        
        if gh_check.returncode != 0:
            return {
                "success": False,
                "error": "GitHub CLI (gh) is not installed. Install from: https://cli.github.com/"
            }
        
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        current_branch = branch_result.stdout.strip()
        
        # Build PR body with metadata
        full_body = body
        
        # Add coverage improvement section
        if coverage_improvement:
            full_body += "\n\n## 📊 Coverage Improvement\n"
            if "before" in coverage_improvement and "after" in coverage_improvement:
                before = coverage_improvement["before"]
                after = coverage_improvement["after"]
                improvement = after - before
                full_body += f"- **Before**: {before:.2f}%\n"
                full_body += f"- **After**: {after:.2f}%\n"
                full_body += f"- **Improvement**: +{improvement:.2f}%\n"
        
        # Add bug fixes section
        if bug_fixes and len(bug_fixes) > 0:
            full_body += "\n\n## 🐛 Bug Fixes\n"
            for bug in bug_fixes:
                full_body += f"- {bug}\n"
        
        # Add automation metadata
        full_body += "\n\n---\n"
        full_body += "*This PR was created by the SE333 Testing Agent*\n"
        full_body += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Create pull request
        pr_result = subprocess.run(
            ["gh", "pr", "create", 
             "--base", base,
             "--head", current_branch,
             "--title", title,
             "--body", full_body],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if pr_result.returncode != 0:
            return {
                "success": False,
                "error": pr_result.stderr,
                "hint": "Make sure you're authenticated with 'gh auth login'"
            }
        
        # Extract PR URL from output
        pr_url = pr_result.stdout.strip()
        
        return {
            "success": True,
            "pr_url": pr_url,
            "base_branch": base,
            "head_branch": current_branch,
            "title": title,
            "message": f"Pull request created successfully: {pr_url}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


#Phase 5: AI Code Review Agent


@mcp.tool()
def run_spotbugs_analysis(project_path: str) -> dict:
    """
    Run SpotBugs static analysis to detect potential bugs.
    """

    try:
        # Run SpotBugs via Maven
        result = subprocess.run(
            ["mvn", "clean", "compile", "spotbugs:spotbugs"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        # Parse SpotBugs XML report
        spotbugs_xml = Path(project_path) / "target/spotbugsXml.xml"
        
        if not spotbugs_xml.exists():
            return {
                "success": False,
                "error": "SpotBugs report not found. Ensure SpotBugs plugin is configured in pom.xml",
                "hint": "Add spotbugs-maven-plugin to your pom.xml"
            }
        
        tree = ET.parse(spotbugs_xml)
        root = tree.getroot()
        
        findings = []
        for bug_instance in root.findall(".//BugInstance"):
            bug = {
                "type": bug_instance.get("type"),
                "priority": bug_instance.get("priority"),
                "category": bug_instance.get("category"),
                "message": bug_instance.find("LongMessage").text if bug_instance.find("LongMessage") is not None else "No message",
                "file": None,
                "line": None
            }
            
            # Get source location
            source_line = bug_instance.find(".//SourceLine")
            if source_line is not None:
                bug["file"] = source_line.get("sourcepath")
                bug["line"] = source_line.get("start")
            
            findings.append(bug)
        
        # Categorize by priority
        high_priority = [f for f in findings if f["priority"] == "1"]
        medium_priority = [f for f in findings if f["priority"] == "2"]
        low_priority = [f for f in findings if f["priority"] == "3"]
        
        return {
            "success": True,
            "total_issues": len(findings),
            "high_priority": len(high_priority),
            "medium_priority": len(medium_priority),
            "low_priority": len(low_priority),
            "findings": findings,
            "high_priority_details": high_priority[:10],  # Top 10
            "summary": f"Found {len(findings)} issues: {len(high_priority)} high, {len(medium_priority)} medium, {len(low_priority)} low priority"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "SpotBugs analysis timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@mcp.tool()
def detect_code_smells(file_path: str) -> dict:
    """
    Analyze a Java file for common code smells.
    """

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        lines = code.split('\n')
        smells = []
        
        # Detect long methods (>50 lines)
        in_method = False
        method_start = 0
        method_name = ""
        brace_count = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Simple method detection
            if '(' in stripped and ')' in stripped and '{' in stripped:
                in_method = True
                method_start = i
                method_name = stripped.split('(')[0].split()[-1]
                brace_count = 1
            elif in_method:
                brace_count += stripped.count('{') - stripped.count('}')
                if brace_count == 0:
                    method_length = i - method_start
                    if method_length > 50:
                        smells.append({
                            "type": "Long Method",
                            "severity": "medium",
                            "line": method_start,
                            "message": f"Method '{method_name}' is {method_length} lines long (>50 lines)",
                            "suggestion": "Consider breaking this method into smaller, focused methods"
                        })
                    in_method = False
            
            # Detect magic numbers
            if stripped and not stripped.startswith('//'):
                import re
                # Look for numeric literals (excluding 0, 1, -1)
                magic_numbers = re.findall(r'\b(?!0\b|1\b|-1\b)\d{2,}\b', stripped)
                if magic_numbers:
                    smells.append({
                        "type": "Magic Number",
                        "severity": "low",
                        "line": i,
                        "message": f"Magic number(s) found: {', '.join(magic_numbers)}",
                        "suggestion": "Replace magic numbers with named constants"
                    })
            
            # Detect large parameter lists (>5 parameters)
            if '(' in stripped and ')' in stripped:
                params = stripped[stripped.index('('):stripped.index(')')].count(',')
                if params > 4:
                    smells.append({
                        "type": "Long Parameter List",
                        "severity": "medium",
                        "line": i,
                        "message": f"Method has {params + 1} parameters (>5)",
                        "suggestion": "Consider using a parameter object or builder pattern"
                    })
            
            # Detect nested conditionals (>3 levels)
            indent_level = (len(line) - len(line.lstrip())) // 4
            if ('if' in stripped or 'for' in stripped or 'while' in stripped) and indent_level > 3:
                smells.append({
                    "type": "Deep Nesting",
                    "severity": "high",
                    "line": i,
                    "message": f"Deep nesting detected (level {indent_level})",
                    "suggestion": "Extract nested logic into separate methods or use early returns"
                })
            
            # Detect commented-out code
            if stripped.startswith('//') and any(keyword in stripped for keyword in ['public', 'private', 'protected', 'class', 'if', 'for', 'while']):
                smells.append({
                    "type": "Commented Code",
                    "severity": "low",
                    "line": i,
                    "message": "Commented-out code detected",
                    "suggestion": "Remove commented code (use version control instead)"
                })
            
            # Detect empty catch blocks
            if 'catch' in stripped and i + 1 < len(lines) and lines[i].strip() == '}':
                smells.append({
                    "type": "Empty Catch Block",
                    "severity": "high",
                    "line": i,
                    "message": "Empty catch block - silently swallowing exceptions",
                    "suggestion": "At minimum, log the exception or rethrow as RuntimeException"
                })
        
        return {
            "success": True,
            "file": file_path,
            "total_smells": len(smells),
            "by_severity": {
                "high": len([s for s in smells if s["severity"] == "high"]),
                "medium": len([s for s in smells if s["severity"] == "medium"]),
                "low": len([s for s in smells if s["severity"] == "low"])
            },
            "smells": smells
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}



if __name__ == "__main__":
    mcp.run(transport="sse")
