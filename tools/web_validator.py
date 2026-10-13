#!/usr/bin/env python3
"""
Tool: web_validator
Pure Python & V8 Web Code Syntax Validator Suite for HTML, CSS, and JavaScript.
Validates syntax, tag nesting, brace matching, and script execution readiness.
Can inspect standalone files (.html, .css, .js) or recursive directories.
"""

import sys
import os
import re
import json
import subprocess
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Tuple

try:
    from tools.base import make_result, cli_runner
except ImportError:
    from base import make_result, cli_runner

TOOL_SPEC = {
    "name": "web_validator",
    "description": "Validate syntax and structure of HTML, CSS, and JavaScript files or code snippets. Detects unclosed tags, CSS syntax errors, and JavaScript syntax errors.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the target file (.html, .css, .js) or directory to inspect."
            },
            "content": {
                "type": "string",
                "description": "Optional inline code content to validate directly."
            },
            "file_type": {
                "type": "string",
                "enum": ["html", "css", "js", "auto"],
                "description": "Type of code if passing inline content. Default is 'auto'."
            }
        },
        "required": ["path"]
    }
}

VOID_HTML_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr"
}

class StrictHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tag_stack: List[Tuple[str, int, int]] = []
        self.errors: List[Dict[str, Any]] = []
        self.styles: List[Tuple[str, int]] = []
        self.scripts: List[Tuple[str, int, Optional[str]]] = []
        self._current_tag = None
        self._tag_start_line = 1
        self.has_doctype = False

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.has_doctype = True

    def handle_starttag(self, tag, attrs):
        line, col = self.getpos()
        tag_lower = tag.lower()
        self._current_tag = tag_lower
        self._tag_start_line = line
        attrs_dict = {k.lower(): v for k, v in attrs if k}

        if tag_lower in VOID_HTML_TAGS:
            return

        if tag_lower == "script":
            script_type = attrs_dict.get("type", "javascript").lower()
            self._current_script_type = script_type
        else:
            self._current_script_type = None

        self.tag_stack.append((tag_lower, line, col))

    def handle_endtag(self, tag):
        line, col = self.getpos()
        tag_lower = tag.lower()
        if tag_lower in VOID_HTML_TAGS:
            return

        if tag_lower == "script":
            self._current_script_type = None

        if not self.tag_stack:
            self.errors.append({
                "type": "HTML_UNMATCHED_CLOSE_TAG",
                "line": line,
                "column": col,
                "message": f"Closing tag </{tag_lower}> found without matching opening tag."
            })
            return

        last_tag, start_line, start_col = self.tag_stack[-1]
        if last_tag == tag_lower:
            self.tag_stack.pop()
        else:
            # Check if matching tag exists deeper in stack
            found_idx = -1
            for idx in range(len(self.tag_stack) - 1, -1, -1):
                if self.tag_stack[idx][0] == tag_lower:
                    found_idx = idx
                    break

            if found_idx != -1:
                # Missing close tags for intermediate elements
                while len(self.tag_stack) > found_idx:
                    unclosed, uline, ucol = self.tag_stack.pop()
                    if unclosed != tag_lower:
                        self.errors.append({
                            "type": "HTML_UNCLOSED_TAG",
                            "line": uline,
                            "column": ucol,
                            "message": f"Tag <{unclosed}> opened at line {uline} was not closed before </{tag_lower}> at line {line}."
                        })
            else:
                self.errors.append({
                    "type": "HTML_MISMATCHED_CLOSE_TAG",
                    "line": line,
                    "column": col,
                    "message": f"Unexpected closing tag </{tag_lower}>. Expected </{last_tag}> (opened at line {start_line})."
                })

    def handle_data(self, data):
        line, col = self.getpos()
        if self._current_tag == "style":
            self.styles.append((data, self._tag_start_line))
        elif self._current_tag == "script":
            self.scripts.append((data, self._tag_start_line, self._current_script_type))

    def close(self):
        super().close()
        # Any remaining unclosed tags
        while self.tag_stack:
            tag, line, col = self.tag_stack.pop()
            self.errors.append({
                "type": "HTML_UNCLOSED_TAG",
                "line": line,
                "column": col,
                "message": f"Unclosed tag <{tag}> opened at line {line}."
            })

def validate_css_code(css_code: str, base_line: int = 1) -> List[Dict[str, Any]]:
    errors = []
    # Strip comments first
    comment_pattern = re.compile(r'/\*.*?\*/', re.DOTALL)
    cleaned_css = comment_pattern.sub(lambda m: '\n' * m.group(0).count('\n'), css_code)

    brace_depth = 0
    lines = cleaned_css.split('\n')
    for idx, line in enumerate(lines):
        line_num = base_line + idx
        for char in line:
            if char == '{':
                brace_depth += 1
            elif char == '}':
                brace_depth -= 1
                if brace_depth < 0:
                    errors.append({
                        "type": "CSS_UNMATCHED_BRACE",
                        "line": line_num,
                        "message": f"Unmatched closing brace '}}' in CSS at line {line_num}."
                    })
                    brace_depth = 0

    if brace_depth > 0:
        errors.append({
            "type": "CSS_UNCLOSED_BRACE",
            "line": base_line + len(lines) - 1,
            "message": f"Unclosed '{brace_depth}' opening brace(s) in CSS block starting at line {base_line}."
        })

    return errors

def validate_js_code(js_code: str, base_line: int = 1, is_module: bool = True) -> List[Dict[str, Any]]:
    errors = []
    if not js_code.strip():
        return errors

    # Check via node --check if node is available
    try:
        cmd = ["node", "--input-type=module" if is_module else "--input-type=commonjs", "--check"]
        proc = subprocess.run(
            cmd,
            input=js_code,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if proc.returncode != 0:
            stderr = proc.stderr
            err_line = base_line
            # Try parsing line number from node error
            match = re.search(r':(\d+)', stderr)
            if match:
                err_line = base_line + int(match.group(1)) - 1
            errors.append({
                "type": "JS_SYNTAX_ERROR",
                "line": err_line,
                "message": stderr.strip().split('\n')[0] if stderr else "JavaScript syntax error."
            })
    except Exception:
        # Fallback pure Python bracket matching
        brackets = {'(': ')', '{': '}', '[': ']'}
        stack = []
        for l_idx, line in enumerate(js_code.split('\n')):
            curr_line = base_line + l_idx
            for char in line:
                if char in brackets.keys():
                    stack.append((char, curr_line))
                elif char in brackets.values():
                    if not stack:
                        errors.append({
                            "type": "JS_UNMATCHED_BRACKET",
                            "line": curr_line,
                            "message": f"Unmatched bracket '{char}' in JavaScript at line {curr_line}."
                        })
                    else:
                        top, tline = stack.pop()
                        if brackets[top] != char:
                            errors.append({
                                "type": "JS_MISMATCHED_BRACKET",
                                "line": curr_line,
                                "message": f"Mismatched bracket: expected '{brackets[top]}', found '{char}' at line {curr_line}."
                            })
        if stack:
            unclosed, uline = stack.pop()
            errors.append({
                "type": "JS_UNCLOSED_BRACKET",
                "line": uline,
                "message": f"Unclosed bracket '{unclosed}' in JavaScript at line {uline}."
            })

    return errors

def validate_file(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {"file": file_path, "success": False, "errors": [{"type": "FILE_NOT_FOUND", "message": "File does not exist."}]}

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {"file": file_path, "success": False, "errors": [{"type": "READ_ERROR", "message": str(e)}]}

    ext = os.path.splitext(file_path)[1].lower()
    errors = []

    if ext in [".html", ".htm"]:
        parser = StrictHTMLParser()
        try:
            parser.feed(content)
            parser.close()
            errors.extend(parser.errors)

            # Validate embedded styles
            for style_content, sline in parser.styles:
                errors.extend(validate_css_code(style_content, base_line=sline))

            # Validate embedded scripts
            for script_content, sline, stype in parser.scripts:
                if stype in ["importmap", "application/json", "json"]:
                    try:
                        if script_content.strip():
                            json.loads(script_content)
                    except Exception as je:
                        errors.append({"type": "JSON_SYNTAX_ERROR", "line": sline, "message": f"Invalid JSON in script type='{stype}': {je}"})
                else:
                    is_mod = (stype == "module" or "import " in script_content or "export " in script_content)
                    errors.extend(validate_js_code(script_content, base_line=sline, is_module=is_mod))

        except Exception as e:
            errors.append({"type": "HTML_PARSE_EXCEPTION", "line": 1, "message": str(e)})

    elif ext == ".css":
        errors.extend(validate_css_code(content, base_line=1))
    elif ext in [".js", ".mjs"]:
        errors.extend(validate_js_code(content, base_line=1, is_module=True))
    else:
        return {"file": file_path, "success": True, "skipped": True, "message": f"Unsupported extension '{ext}'."}

    return {
        "file": file_path,
        "success": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors
    }

def validate_target(path: str, content: Optional[str] = None, file_type: str = "auto") -> Dict[str, Any]:
    if content is not None:
        if file_type == "auto":
            file_type = "html" if "<html" in content or "<!doctype" in content.lower() else "js"
        # Validate inline
        errors = []
        if file_type == "html":
            parser = StrictHTMLParser()
            parser.feed(content)
            parser.close()
            errors.extend(parser.errors)
        elif file_type == "css":
            errors.extend(validate_css_code(content))
        elif file_type in ["js", "javascript"]:
            errors.extend(validate_js_code(content))
        return make_result(len(errors) == 0, data={"errors": errors, "error_count": len(errors)})

    if os.path.isdir(path):
        results = []
        total_errors = 0
        for root, _, files in os.walk(path):
            for f in files:
                if f.endswith((".html", ".htm", ".css", ".js", ".mjs")):
                    fpath = os.path.join(root, f)
                    res = validate_file(fpath)
                    results.append(res)
                    total_errors += res.get("error_count", 0)

        all_ok = (total_errors == 0)
        return make_result(all_ok, data={
            "target": path,
            "type": "directory",
            "files_checked": len(results),
            "total_errors": total_errors,
            "details": results
        })

    res = validate_file(path)
    return make_result(res.get("success", False), data=res)

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    path = params.get("path", "")
    content = params.get("content")
    file_type = params.get("file_type", "auto")
    return validate_target(path, content, file_type)

if __name__ == "__main__":
    cli_runner(
        tool_name="web_validator",
        tool_spec=TOOL_SPEC,
        execute_fn=execute
    )
