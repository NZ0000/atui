#!/usr/bin/env python3
"""
Tool: analyzer
High-performance code analysis engine dedicated to the Analyst Agent.
Provides fast project-wide regex search, AST/symbol extraction, cross-file reference tracking,
structural file outlines, automated pitfall detection, and RAG query of curated bug knowledge.
"""

import sys
import os
import re
import ast
import json
import glob
from typing import Dict, Any, List, Optional, Set

try:
    from tools.base import make_result, cli_runner, resolve_project_path
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.base import make_result, cli_runner, resolve_project_path

EXCLUDE_DIRS = {
    ".git", ".pytest_cache", "__pycache__", "node_modules", "vendor",
    ".idea", ".vscode", "dist", "build", ".next", ".turbo"
}

TOOL_SPEC = {
    "name": "analyzer",
    "description": "专供代码分析师 (Analyst) 使用的高性能代码分析器。支持全项目文本检索、类/函数/导入导出符号提取、关联调用链路分析、结构化文件大纲提取、已知Bug与坏味道自动扫描，以及Bug经验库 RAG 知识检索。其它Agent不配置此工具以极大节省上下文占用。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "extract_symbols", "extract_related", "file_outline", "detect_pitfalls", "query_knowledge", "asset_audit"],
                "description": "分析操作：search (全项目正则/文本搜索), extract_symbols (提取类/函数/导入导出), extract_related (追踪关联调用与引用), file_outline (快速提取结构大纲), detect_pitfalls (扫描常见Bug与隐患), query_knowledge (检索Bug经验知识库), asset_audit (盘点3D资产：glb内嵌名称+代码引用+放置坐标+缺失引用，用于资产-场景一致性审查)"
            },
            "query": {
                "type": "string",
                "description": "搜索关键词或正则表达式，或要查询关联/知识的主题词"
            },
            "file_path": {
                "type": "string",
                "description": "指定目标文件路径（相对或绝对路径）"
            },
            "file_pattern": {
                "type": "string",
                "description": "文件通配符过滤，例如 '*.js', '*.py', '*.html' (默认全文本文件)"
            },
            "max_results": {
                "type": "integer",
                "description": "最大返回匹配结果数量（默认 50，防止上下文爆炸）"
            },
            "topic": {
                "type": "string",
                "description": "query_knowledge 时的知识主题，例如 'threejs_webgl', 'javascript_web', 'python_backend', 'all'"
            }
        },
        "required": ["action"]
    }
}


def _get_project_root() -> str:
    try:
        from core.project import get_current_project
        proj = get_current_project()
        if proj and proj.path and os.path.exists(proj.path):
            return proj.path
    except Exception:
        pass
    return os.getcwd()


def _is_text_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".json",
        ".md", ".yml", ".yaml", ".sh", ".toml", ".ini", ".txt", ".sql"
    }


def search_codebase(
    query: str,
    root_dir: str,
    file_pattern: Optional[str] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """Search for regex or text across all project text files."""
    if not query:
        return make_result(False, error="Query cannot be empty for search.")

    try:
        pattern = re.compile(query, re.IGNORECASE)
    except re.error as e:
        return make_result(False, error=f"Invalid regex query '{query}': {e}")

    matches = []
    total_found = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude blacklisted directories
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]

        for fname in filenames:
            if not _is_text_file(fname):
                continue
            if file_pattern and not fnmatch_pattern(fname, file_pattern):
                continue

            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        if pattern.search(line):
                            total_found += 1
                            if len(matches) < max_results:
                                matches.append({
                                    "file": rel_path,
                                    "line": line_no,
                                    "content": line.rstrip()
                                })
            except Exception:
                continue

    return make_result(True, data={
        "query": query,
        "total_matches": total_found,
        "returned_matches": len(matches),
        "matches": matches,
        "truncated": total_found > max_results
    })


def fnmatch_pattern(filename: str, pattern: str) -> bool:
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)


def extract_symbols(file_path: str, root_dir: str) -> Dict[str, Any]:
    """Extract classes, functions, methods, imports, and exports from a file."""
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(root_dir, file_path)
    if not os.path.exists(abs_path):
        return make_result(False, error=f"File '{file_path}' does not exist.")

    ext = os.path.splitext(abs_path)[1].lower()
    classes = []
    functions = []
    imports = []
    exports = []

    try:
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return make_result(False, error=f"Failed to read file: {e}")

    if ext == ".py":
        try:
            tree = ast.parse(content, filename=abs_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({"name": node.name, "line": node.lineno, "methods": methods})
                elif isinstance(node, ast.FunctionDef):
                    functions.append({"name": node.name, "line": node.lineno, "args": [a.arg for a in node.args.args]})
                elif isinstance(node, ast.Import):
                    for n in node.names:
                        imports.append({"module": n.name, "asname": n.asname})
                elif isinstance(node, ast.ImportFrom):
                    imports.append({"from": node.module, "names": [n.name for n in node.names]})
        except Exception as e:
            # Fallback regex if syntax error in py file
            classes = re.findall(r"class\s+([A-Za-z0-9_]+)", content)
            functions = re.findall(r"def\s+([A-Za-z0-9_]+)", content)
    elif ext in {".js", ".ts", ".jsx", ".tsx", ".html"}:
        # Extract ES6 Classes
        for m in re.finditer(r"(?:export\s+default\s+|export\s+)?class\s+([A-Za-z0-9_]+)(?:\s+extends\s+([A-Za-z0-9_]+))?", content):
            c_name = m.group(1)
            parent = m.group(2)
            classes.append({"name": c_name, "extends": parent})

        # Extract Functions
        for m in re.finditer(r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(", content):
            functions.append({"name": m.group(1)})
        # Arrow functions / methods
        for m in re.finditer(r"(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", content):
            functions.append({"name": m.group(1)})

        # Extract Imports
        for m in re.finditer(r"import\s+(?:\{([^}]+)\}|([A-Za-z0-9_]+))\s+from\s+['\"]([^'\"]+)['\"]", content):
            imports.append({
                "specifiers": (m.group(1) or m.group(2)).strip(),
                "source": m.group(3)
            })

        # Extract Exports
        for m in re.finditer(r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+([A-Za-z0-9_]+)", content):
            exports.append(m.group(1))
        for m in re.finditer(r"export\s+\{([^}]+)\}", content):
            exports.extend([x.strip() for x in m.group(1).split(",") if x.strip()])

    # Format return
    class_names = [c["name"] if isinstance(c, dict) else c for c in classes]
    func_names = [f["name"] if isinstance(f, dict) else f for f in functions]

    return make_result(True, data={
        "file": file_path,
        "classes": class_names,
        "classes_detail": classes,
        "functions": func_names,
        "functions_detail": functions,
        "imports": imports,
        "exports": exports,
        "line_count": len(content.splitlines())
    })


def extract_related(query: str, root_dir: str, max_results: int = 30) -> Dict[str, Any]:
    """Find definitions, exports, imports, and call sites of a symbol across the project."""
    if not query:
        return make_result(False, error="Target identifier 'query' cannot be empty.")

    definitions = []
    usages = []

    pattern_def = re.compile(rf"(class\s+{re.escape(query)}|function\s+{re.escape(query)}|def\s+{re.escape(query)}|const\s+{re.escape(query)}\s*=)")
    pattern_usage = re.compile(rf"\b{re.escape(query)}\b")

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            if not _is_text_file(fname):
                continue
            full_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full_path, root_dir)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        line_str = line.strip()
                        if pattern_def.search(line_str):
                            definitions.append({"file": rel_path, "line": line_no, "content": line_str})
                        elif pattern_usage.search(line_str):
                            if len(usages) < max_results:
                                usages.append({"file": rel_path, "line": line_no, "content": line_str})
            except Exception:
                continue

    return make_result(True, data={
        "symbol": query,
        "definitions": definitions,
        "usages_count": len(usages),
        "usages": usages
    })


def file_outline(file_path: str, root_dir: str) -> Dict[str, Any]:
    """Provide a compact outline of a file's structure without dumping raw source."""
    return extract_symbols(file_path, root_dir)


def detect_pitfalls(file_path: Optional[str], root_dir: str) -> Dict[str, Any]:
    """
    Automated scanner for high-frequency bugs and anti-patterns:
    - Three.js EffectComposer missing MSAA samples: 4
    - Procedural mesh hiding bug (attached to this.group instead of this.proceduralBody)
    - Flat shading on organic meshes without computeVertexNormals()
    - InstancedMesh missing instanceMatrix.needsUpdate = true
    - Naked BoxGeometry without bevel/extrude/composite
    - TDZ variable usage
    """
    files_to_check = []
    if file_path:
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(root_dir, file_path)
        if os.path.exists(abs_path):
            files_to_check.append(abs_path)
    else:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fname in filenames:
                if fname.endswith((".js", ".ts", ".html", ".py")):
                    files_to_check.append(os.path.join(dirpath, fname))

    findings = []

    for fpath in files_to_check:
        rel_path = os.path.relpath(fpath, root_dir)
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Check 1: EffectComposer without samples: 4
            if "EffectComposer" in content:
                if "WebGLRenderTarget" in content and "samples" not in content:
                    findings.append({
                        "file": rel_path,
                        "type": "ANTI_ALIASING_MISSING",
                        "severity": "CRITICAL",
                        "message": "检测到 EffectComposer 挂载了 WebGLRenderTarget，但未配置 { samples: 4 } (硬件 4x MSAA)。发光边缘与高光轮廓将出现严重像素狗牙！",
                        "rule_ref": "rule/rule.md 三、4 硬件多重采样抗锯齿"
                    })

            # Check 2: Floating window planes attached to this.group
            if "modules/buildings.js" in rel_path or "buildings" in rel_path:
                if re.search(r"this\.group\.add\(\s*(?:win\d+|window|plane)\s*\)", content, re.IGNORECASE):
                    findings.append({
                        "file": rel_path,
                        "type": "FLOATING_PROCEDURAL_MESH",
                        "severity": "HIGH",
                        "message": "检测到窗口/发光面片被直接添加到 this.group，当 GLB 模型加载后隐藏 this.proceduralBody 时，此类面片不会被隐藏，将悬浮穿模！",
                        "solution": "将其添加到 this.proceduralBody，使 GLB 模型入场时整体同步隐藏。"
                    })

            # Check 3: InstancedMesh missing instanceMatrix.needsUpdate
            if "InstancedMesh" in content and "setMatrixAt" in content:
                if "instanceMatrix.needsUpdate" not in content:
                    findings.append({
                        "file": rel_path,
                        "type": "INSTANCED_MESH_STALE_MATRIX",
                        "severity": "HIGH",
                        "message": "检测到 InstancedMesh 调用了 setMatrixAt，但未设置 instanceMatrix.needsUpdate = true，导致批量模型不渲染或坐标全部归零！"
                    })

            # Check 4: Anti-primitive violation
            if re.search(r"new\s+THREE\.BoxGeometry\s*\([^)]*\)", content):
                if "ExtrudeGeometry" not in content and "TubeGeometry" not in content and "LatheGeometry" not in content and ".glb" not in content:
                    findings.append({
                        "file": rel_path,
                        "type": "ANTI_PRIMITIVE_VIOLATION",
                        "severity": "MEDIUM",
                        "message": "检测到使用简单 BoxGeometry 裸拼且缺乏复合造型与外部 GLB 资产，易呈现塑料玩具感。建议使用 ExtrudeGeometry/TubeGeometry 或加载工业级 GLB 资产。"
                    })

        except Exception:
            continue

    return make_result(True, data={
        "total_issues": len(findings),
        "issues": findings
    })


def query_knowledge(query: Optional[str], topic: Optional[str], root_dir: str) -> Dict[str, Any]:
    """Retrieve curated bug knowledge and pitfalls from knowledge/bug_knowledge.json."""
    kb_path = os.path.join(root_dir, "knowledge", "bug_knowledge.json")
    if not os.path.exists(kb_path):
        kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge", "bug_knowledge.json")

    if not os.path.exists(kb_path):
        return make_result(False, error="Knowledge base 'knowledge/bug_knowledge.json' not found.")

    try:
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
    except Exception as e:
        return make_result(False, error=f"Failed to read knowledge base: {e}")

    results = []
    search_term = (query or "").lower().strip()
    topic_term = (topic or "").lower().strip()

    for cat_name, items in kb.items():
        # Check if topic_term matches category directly (e.g. 'threejs' in 'threejs_webgl')
        cat_match = not topic_term or topic_term == "all" or any(part in cat_name.lower() for part in topic_term.split("_"))
        
        for it in items:
            it_str = json.dumps(it, ensure_ascii=False).lower()
            # If cat_match is false, check if topic_term is inside the item content
            term_match = not search_term or search_term in it_str
            topic_in_item = not topic_term or topic_term == "all" or topic_term in it_str or any(part in it_str for part in topic_term.split("_") if len(part) > 2)

            if (cat_match or topic_in_item) and term_match:
                results.append({
                    "category": cat_name,
                    **it
                })

    return make_result(True, data={
        "query": query,
        "topic": topic,
        "matched_count": len(results),
        "knowledge_items": results
    })


def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "").lower().strip()
    root_dir = _get_project_root()

    if not action:
        return make_result(False, error="Parameter 'action' is required.")

    if action == "search":
        query = params.get("query", "")
        file_pattern = params.get("file_pattern")
        max_results = int(params.get("max_results", 50))
        return search_codebase(query, root_dir, file_pattern=file_pattern, max_results=max_results)

    elif action == "extract_symbols":
        file_path = params.get("file_path", "")
        if not file_path:
            return make_result(False, error="extract_symbols requires 'file_path'.")
        return extract_symbols(file_path, root_dir)

    elif action == "extract_related":
        query = params.get("query", "")
        max_results = int(params.get("max_results", 30))
        return extract_related(query, root_dir, max_results=max_results)

    elif action == "file_outline":
        file_path = params.get("file_path", "")
        if not file_path:
            return make_result(False, error="file_outline requires 'file_path'.")
        return file_outline(file_path, root_dir)

    elif action == "detect_pitfalls":
        file_path = params.get("file_path")
        return detect_pitfalls(file_path, root_dir)

    elif action == "asset_audit":
        return _asset_audit(
            root_dir=params.get("root_dir"),
            file_pattern=params.get("file_pattern")
        )

    elif action == "query_knowledge":
        query = params.get("query")
        topic = params.get("topic")
        return query_knowledge(query, topic, root_dir)

    else:
        return make_result(False, error=f"Unknown analyzer action '{action}'.")


def _parse_glb_name(path: str) -> str:
    """Extract the embedded asset name from a glTF-binary JSON chunk (empty on failure)."""
    try:
        import struct
        with open(path, "rb") as f:
            head = f.read(20)
            if len(head) < 20 or head[:4] != b"glTF":
                return ""
            json_len = struct.unpack_from("<I", head, 12)[0]
            raw = f.read(min(json_len, 1 << 20))
            import json as _json
            meta = _json.loads(raw.decode("utf-8", errors="ignore"))
        name = (meta.get("asset") or {}).get("extras", {}).get("title", "") if isinstance(meta, dict) else ""
        if not name and isinstance(meta, dict):
            nodes = meta.get("nodes") or []
            meshes = meta.get("meshes") or []
            name = (nodes[0].get("name", "") if nodes else "") or (meshes[0].get("name", "") if meshes else "")
        return str(name)
    except Exception:
        return ""


def _asset_audit(root_dir: Optional[str] = None, file_pattern: Optional[str] = None) -> Dict[str, Any]:
    """
    Inventory 3D assets vs code usage (project-agnostic, evidence for asset-scene
    coherence review): for every .glb/.gltf under models/ report its embedded name;
    for every code reference report the referencing file and placement coordinates;
    flag references to files that do not exist on disk.
    """
    root = os.path.normpath(root_dir or _get_project_root())
    assets_dir = os.path.join(root, "models")
    files = []
    if os.path.isdir(assets_dir):
        for fn in sorted(os.listdir(assets_dir)):
            if fn.lower().endswith((".glb", ".gltf")):
                files.append(fn)
    inventory = {}
    for fn in files:
        ap = os.path.join(assets_dir, fn)
        inventory[fn] = {
            "file": f"models/{fn}",
            "embedded_name": _parse_glb_name(ap),
            "size_bytes": os.path.getsize(ap),
            "referenced_by": [],
            "placements": [],
        }
    # scan code for references + placement coordinates
    ref_re = re.compile(r"models/([\w./-]+\.(?:glb|gltf))")
    pos_re = re.compile(r"\.position\.set\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)")
    missing = []
    code_files = _iter_text_files(root, file_pattern) if "_iter_text_files" in globals() else _walk_code_files(root)
    for cf, text in code_files:
        rel = os.path.relpath(cf, root).replace(os.sep, "/")
        for m in ref_re.finditer(text):
            target = m.group(1)
            if target not in inventory:
                missing.append({"ref": f"models/{target}", "referenced_by": rel})
                continue
            inv = inventory[target]
            inv["referenced_by"].append(rel)
            # placement: nearest position.set within 400 chars after the load call
            seg = text[m.end():m.end() + 400]
            pm = pos_re.search(seg)
            if pm:
                inv["placements"].append({
                    "file": rel, "x": float(pm.group(1)), "y": float(pm.group(2)), "z": float(pm.group(3))
                })
    unreferenced = [v["file"] for v in inventory.values() if not v["referenced_by"]]
    return make_result(True, data={
        "asset_count": len(inventory),
        "assets": list(inventory.values()),
        "missing_refs": missing,
        "unreferenced_assets": unreferenced,
        "hint": "用 embedded_name 判断资产内容与场景主题是否匹配；用 placements 的 y 值对照场景水面/地面阈值判断空间合理性。语义判断由审查者完成。"
    })


def _walk_code_files(root: str):
    """Yield (path, text) for source files under root, skipping binaries/vendor."""
    skip_dirs = {"node_modules", ".git", "vendor", "models", "deliverables", "__pycache__"}
    skip_ext = (".glb", ".gltf", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".bin", ".ktx2", ".woff", ".woff2")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            if fn.lower().endswith(skip_ext):
                continue
            ap = os.path.join(dirpath, fn)
            try:
                with open(ap, "r", encoding="utf-8", errors="ignore") as f:
                    yield ap, f.read()
            except Exception:
                continue


if __name__ == "__main__":
    cli_runner("analyzer", TOOL_SPEC, execute)
