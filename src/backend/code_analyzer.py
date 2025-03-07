import ast
import astroid
from pylint.lint import Run
from pylint.reporters import JSONReporter
from io import StringIO
import sys
import tokenize
from typing import List, Dict
import tempfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.common_performance_patterns = {
            "nested_loops": (
                ast.For,
                "Nested loops detected. Consider optimizing or using alternative approaches."
            ),
            "multiple_ifs": (
                ast.If,
                "Multiple nested if statements. Consider consolidating conditions."
            ),
            "list_comprehension": (
                ast.For,
                "Consider using list comprehension for better performance."
            )
        }

    def find_errors(self, code: str) -> List[Dict]:
        errors = []
        temp_file = None
        
        # Syntax error check
        try:
            ast.parse(code)
        except SyntaxError as e:
            return [{
                "type": "SyntaxError",
                "line": e.lineno,
                "message": str(e),
                "severity": "error"
            }]

        # Pylint analysis
        try:
            # Create temporary file with a unique name
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False,
                encoding='utf-8'
            )
            temp_file.write(code)
            temp_file.close()  # Close the file before Pylint reads it
            
            reporter = JSONReporter()
            Run([temp_file.name], reporter=reporter, do_exit=False)
            
            for message in reporter.messages:
                errors.append({
                    "type": message.symbol,
                    "line": message.line,
                    "message": message.msg,
                    "severity": message.category.lower()
                })
            
        except Exception as e:
            logger.error(f"Error during code analysis: {str(e)}")
            errors.append({
                "type": "AnalysisError",
                "line": 0,
                "message": f"Failed to analyze code: {str(e)}",
                "severity": "error"
            })
            
        finally:
            # Clean up the temporary file
            if temp_file:
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {temp_file.name}: {str(e)}")

        return errors

    def analyze_performance(self, code: str) -> List[Dict]:
        performance_issues = []
        try:
            tree = ast.parse(code)
            self._analyze_node(tree, performance_issues)
        except Exception as e:
            performance_issues.append({
                "type": "AnalysisError",
                "message": f"Failed to analyze performance: {str(e)}",
                "line": 0,
                "suggestion": "Ensure the code is syntactically correct."
            })
        return performance_issues

    def _analyze_node(self, node: ast.AST, issues: List[Dict], depth: int = 0):
        # Track nested loops
        if isinstance(node, ast.For) or isinstance(node, ast.While):
            if depth > 0:
                issues.append({
                    "type": "NestedLoop",
                    "line": node.lineno,
                    "message": "Nested loop detected",
                    "suggestion": "Consider using alternative approaches like list comprehension or vectorized operations."
                })

        # Check for inefficient list operations
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == 'append' and isinstance(node.func.value, ast.Name):
                    # Check if append is used in a loop
                    if self._is_in_loop(node):
                        issues.append({
                            "type": "IneffientListOperation",
                            "line": node.lineno,
                            "message": "List append in loop",
                            "suggestion": "Consider using list comprehension or pre-allocating the list."
                        })

        # Recursively analyze child nodes
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                self._analyze_node(child, issues, depth + 1)
            else:
                self._analyze_node(child, issues, depth)

    def _is_in_loop(self, node: ast.AST) -> bool:
        parent = node
        while hasattr(parent, 'parent'):
            parent = parent.parent
            if isinstance(parent, (ast.For, ast.While)):
                return True
        return False

    def get_code_complexity(self, code: str) -> Dict:
        tree = ast.parse(code)
        complexity = {
            "cyclomatic": 0,
            "number_of_functions": 0,
            "lines_of_code": len(code.splitlines())
        }
        
        # Count decision points for cyclomatic complexity
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity["cyclomatic"] += 1
            elif isinstance(node, ast.FunctionDef):
                complexity["number_of_functions"] += 1
                
        return complexity 