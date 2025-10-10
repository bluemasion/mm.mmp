#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# project_context_generator.py
"""
项目上下文快照生成器
为大语言模型多轮会话提供完整的项目理解上下文
"""
import os
import ast
import json
import sqlite3
from datetime import datetime
import glob

class ProjectContextGenerator:
    """项目上下文生成器"""
    
    def __init__(self, project_root="."):
        self.project_root = project_root
        self.context_data = {}
        
    def generate_full_context(self):
        """生成完整的项目上下文快照"""
        print("🔄 生成项目上下文快照...")
        
        context = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project_root": os.path.abspath(self.project_root),
                "generator_version": "1.0"
            }
        }
        
        print("� 收集环境信息...")
        context["environment"] = self._collect_environment_info()
        
        print("�📚 加载核心文档...")
        context["documents"] = self._load_core_documents()
        
        print("🏗️ 分析代码结构...")
        context["code_structure"] = self._analyze_code_structure()
        
        print("💾 分析数据库结构...")
        context["database_structure"] = self._analyze_database_schema()
        
        print("📊 收集项目统计...")
        context["project_stats"] = self._collect_project_statistics()
        
        print("🔍 检测最近变更...")
        context["recent_changes"] = self._detect_recent_changes()
        
        print("🎯 构建开发上下文...")
        context["development_context"] = self._build_development_context()
        
        return context
    
    def _collect_environment_info(self):
        """收集环境和依赖信息"""
        env_info = {}
        
        # Python版本信息
        import sys
        env_info["python_version"] = {
            "version": sys.version,
            "version_info": "{}.{}.{}".format(*sys.version_info[:3]),
            "executable": sys.executable
        }
        
        # 读取requirements.txt
        if os.path.exists("requirements.txt"):
            try:
                with open("requirements.txt", 'r', encoding='utf-8') as f:
                    requirements_content = f.read()
                    # 解析主要依赖
                    main_deps = []
                    for line in requirements_content.split('\n'):
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('-'):
                            if '==' in line or '>=' in line:
                                main_deps.append(line)
                    env_info["dependencies"] = {
                        "total_requirements": len(main_deps),
                        "main_packages": main_deps[:15],  # 显示前15个主要包
                        "requirements_file_size": len(requirements_content)
                    }
            except Exception as e:
                env_info["dependencies"] = {"error": "Error reading requirements.txt: " + str(e)}
        else:
            env_info["dependencies"] = {"error": "requirements.txt not found"}
        
        # 操作系统信息
        import platform
        env_info["system"] = {
            "platform": platform.platform(),
            "system": platform.system(),
            "architecture": platform.architecture()[0]
        }
        
        return env_info
    
    def _load_core_documents(self):
        """加载核心项目文档"""
        documents = {}
        
        # 核心文档列表
        core_docs = [
            "智能分类推荐功能需求与使用指南.md",
            "ARCHITECTURE_REFACTORING_PLAN.md",
            "DATABASE_ENHANCEMENT_REPORT.md",
            "PROJECT_COMPLETION_SUMMARY.md",
            "README.md"
        ]
        
        for doc in core_docs:
            if os.path.exists(doc):
                try:
                    with open(doc, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # 限制长度避免过长
                        if len(content) > 2000:
                            content = content[:2000] + "\n..."
                        documents[doc] = content
                except Exception as e:
                    documents[doc] = "Error loading: " + str(e)
        
        return documents
    
    def _analyze_code_structure(self):
        """分析代码结构"""
        structure = {
            "main_modules": [],
            "app_modules": []
        }
        
        # 分析主模块
        for py_file in glob.glob("*.py"):
            analysis = self._analyze_python_file(py_file)
            if analysis:
                structure["main_modules"].append(analysis)
        
        # 分析app模块
        app_dir = os.path.join(self.project_root, "app")
        if os.path.exists(app_dir):
            for py_file in glob.glob(os.path.join(app_dir, "*.py")):
                analysis = self._analyze_python_file(py_file)
                if analysis:
                    structure["app_modules"].append(analysis)
        
        return structure
    
    def _analyze_python_file(self, file_path):
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            tree = ast.parse(content)
            
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:  # 只统计顶级函数
                    functions.append(node.name)
            
            # 获取模块文档字符串
            docstring = ""
            if (tree.body and isinstance(tree.body[0], ast.Expr) 
                and isinstance(tree.body[0].value, ast.Str)):
                docstring = tree.body[0].value.s
            elif (tree.body and isinstance(tree.body[0], ast.Expr)
                  and isinstance(tree.body[0].value, ast.Constant)
                  and isinstance(tree.body[0].value.value, str)):
                docstring = tree.body[0].value.value
            
            lines = len(content.splitlines())
            
            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "classes": len(classes),
                "functions": len(functions),
                "lines": lines,
                "docstring": docstring.strip() if docstring else ""
            }
        except Exception as e:
            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "error": str(e)
            }
    
    def _analyze_database_schema(self):
        """分析数据库结构"""
        databases = {}
        
        # 查找所有.db文件
        for db_file in glob.glob("*.db"):
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                db_info = {}
                for table in tables:
                    table_name = table[0]
                    
                    # 获取表结构
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    # 获取行数
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    db_info[table_name] = {
                        "columns": len(columns),
                        "rows": row_count
                    }
                
                databases[db_file] = db_info
                conn.close()
                
            except Exception as e:
                databases[db_file] = {"error": str(e)}
        
        return databases
    
    def _collect_project_statistics(self):
        """收集项目统计信息"""
        stats = {
            "file_counts": {},
            "code_metrics": {
                "python_files": 0,
                "total_lines": 0,
                "total_classes": 0,
                "total_functions": 0
            }
        }
        
        # 统计文件类型
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext:
                    stats["file_counts"][ext] = stats["file_counts"].get(ext, 0) + 1
        
        # 统计Python代码指标
        for py_file in glob.glob("*.py") + glob.glob("app/*.py"):
            if os.path.exists(py_file):
                analysis = self._analyze_python_file(py_file)
                if "error" not in analysis:
                    stats["code_metrics"]["python_files"] += 1
                    stats["code_metrics"]["total_lines"] += analysis.get("lines", 0)
                    stats["code_metrics"]["total_classes"] += analysis.get("classes", 0)
                    stats["code_metrics"]["total_functions"] += analysis.get("functions", 0)
        
        return stats
    
    def _detect_recent_changes(self):
        """检测最近的文件变更"""
        changes = []
        
        # 获取最近修改的文件
        all_files = []
        for root, dirs, files in os.walk(self.project_root):
            for file in files:
                if not file.startswith('.') and file.endswith(('.py', '.md', '.json', '.yml', '.yaml')):
                    file_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(file_path)
                        all_files.append((file_path, mtime))
                    except OSError:
                        pass
        
        # 按修改时间排序，取最近10个
        all_files.sort(key=lambda x: x[1], reverse=True)
        recent_files = all_files[:10]
        
        for file_path, mtime in recent_files:
            changes.append({
                "file": os.path.relpath(file_path, self.project_root),
                "modified": datetime.fromtimestamp(mtime).isoformat()
            })
        
        return changes
    
    def _build_development_context(self):
        """构建开发上下文信息"""
        context = {
            "main_features": [
                "智能分类推荐",
                "多源融合匹配（关键词、制造商、规格模式）",
                "TF-IDF相似度计算",
                "训练数据管理",
                "Web界面"
            ],
            "known_issues": [
                "分类体系需持续扩展",
                "训练数据需定期更新",
                "上下文快照机制需完善"
            ],
            "next_steps": [
                "完善上下文快照系统",
                "优化分类算法准确率", 
                "扩展多语言支持"
            ]
        }
        
        return context
    
    def save_context_snapshot(self, context, filename=None):
        """保存上下文快照为Markdown文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = "PROJECT_CONTEXT_SNAPSHOT_{}.md".format(timestamp)
        
        print("💾 保存上下文快照到 {}...".format(filename))
        
        markdown_content = self._generate_markdown_context(context)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print("✅ 上下文快照已保存: {}".format(filename))
        return filename
    
    def _generate_markdown_context(self, context):
        """生成Markdown格式的上下文文档"""
        md = []
        
        # 标题和元数据
        md.append("# MMP项目上下文快照")
        md.append("> 生成时间: " + context['metadata']['generated_at'])
        md.append("> 生成器版本: " + context['metadata']['generator_version'])
        md.append("")
        
        # 项目概览
        md.append("## 🎯 项目概览")
        md.append("构建基于数据库的物料主数据智能分类推荐系统")
        md.append("")
        md.append("**当前阶段**: 数据库化完成，智能分类系统优化阶段")
        md.append("")
        md.append("**核心技术**: Python, Flask, SQLite, scikit-learn, TF-IDF, jieba")
        md.append("")
        
        # 环境信息
        if context.get("environment"):
            env = context["environment"]
            md.append("## 🐍 开发环境")
            md.append("")
            
            # Python版本
            if env.get("python_version"):
                py_info = env["python_version"]
                md.append("### Python环境")
                md.append("- **版本**: " + py_info.get("version_info", "未知"))
                md.append("- **完整版本**: " + py_info.get("version", "未知").replace('\n', ' '))
                md.append("- **执行路径**: " + py_info.get("executable", "未知"))
                md.append("")
            
            # 系统信息
            if env.get("system"):
                sys_info = env["system"]
                md.append("### 系统环境")
                md.append("- **平台**: " + sys_info.get("platform", "未知"))
                md.append("- **系统**: " + sys_info.get("system", "未知"))
                md.append("- **架构**: " + sys_info.get("architecture", "未知"))
                md.append("")
            
            # 依赖信息
            if env.get("dependencies"):
                deps = env["dependencies"]
                if "error" not in deps:
                    md.append("### 项目依赖")
                    md.append("- **依赖包数量**: " + str(deps.get("total_requirements", 0)))
                    md.append("- **requirements.txt大小**: " + str(deps.get("requirements_file_size", 0)) + " 字符")
                    md.append("")
                    md.append("**主要依赖包:**")
                    for pkg in deps.get("main_packages", []):
                        md.append("- " + pkg)
                    md.append("")
                else:
                    md.append("### 依赖信息")
                    md.append("- **状态**: " + deps.get("error", "未知错误"))
                    md.append("")
        
        # 核心文档摘要
        if context.get("documents"):
            md.append("## 📚 核心文档摘要")
            md.append("")
            for doc_name, content in context["documents"].items():
                md.append(f"### {doc_name}")
                md.append("```")
                md.append(content)
                md.append("```")
                md.append("")
        
        # 代码结构概览
        if context.get("code_structure"):
            md.append("## 🏗️ 代码结构概览")
            md.append("")
            
            # 主模块
            main_modules = context["code_structure"].get("main_modules", [])
            if main_modules:
                md.append(f"### 主模块 ({len(main_modules)} 个)")
                for module in main_modules:
                    md.append(f"- **{module['name']}**: {module.get('classes', 0)}个类, {module.get('functions', 0)}个函数, {module.get('lines', 0)}行")
                    if module.get('docstring'):
                        md.append(f"  > {module['docstring']}")
                md.append("")
            
            # App模块
            app_modules = context["code_structure"].get("app_modules", [])
            if app_modules:
                md.append(f"### App模块 ({len(app_modules)} 个)")
                for module in app_modules:
                    md.append(f"- **{module['name']}**: {module.get('classes', 0)}个类, {module.get('functions', 0)}个函数, {module.get('lines', 0)}行")
                    if module.get('docstring'):
                        md.append(f"  > {module['docstring']}")
                md.append("")
        
        # 数据库结构
        if context.get("database_structure"):
            md.append("## 💾 数据库结构")
            md.append("")
            for db_name, tables in context["database_structure"].items():
                md.append(f"### {db_name}")
                if "error" in tables:
                    md.append(f"- 错误: {tables['error']}")
                else:
                    for table_name, info in tables.items():
                        md.append(f"- **{table_name}**: {info['columns']}列, {info['rows']}行数据")
                md.append("")
        
        # 项目统计
        if context.get("project_stats"):
            stats = context["project_stats"]
            md.append("## 📊 项目统计")
            md.append("")
            
            # 文件统计
            if stats.get("file_counts"):
                md.append("### 文件统计")
                for ext, count in stats["file_counts"].items():
                    md.append(f"- {ext} 文件: {count} 个")
                md.append("")
            
            # 代码度量
            if stats.get("code_metrics"):
                metrics = stats["code_metrics"]
                md.append("### 代码度量")
                md.append(f"- Python文件: {metrics['python_files']} 个")
                md.append(f"- 总代码行数: {metrics['total_lines']} 行")
                md.append(f"- 类总数: {metrics['total_classes']} 个  ")
                md.append(f"- 函数总数: {metrics['total_functions']} 个")
                md.append("")
        
        # 最近变更
        if context.get("recent_changes"):
            md.append("## 🔄 最近变更")
            for change in context["recent_changes"]:
                md.append(f"- {change['file']} ({change['modified']})")
            md.append("")
        
        # 开发上下文
        if context.get("development_context"):
            dev_ctx = context["development_context"]
            md.append("## 🎯 开发上下文")
            md.append("")
            
            md.append("### 主要功能")
            for feature in dev_ctx.get("main_features", []):
                md.append(f"- {feature}")
            md.append("")
            
            md.append("### 已知问题")
            for issue in dev_ctx.get("known_issues", []):
                md.append(f"- {issue}")
            md.append("")
            
            md.append("### 下一步计划")
            for step in dev_ctx.get("next_steps", []):
                md.append(f"- {step}")
            md.append("")
        
        md.append("---")
        md.append("*此上下文快照用于大语言模型多轮会话的项目理解和开发连续性保障*")
        
        return "\n".join(md)


def main():
    """主函数"""
    print("🚀 MMP项目上下文快照生成器")
    print("=" * 50)
    
    # 创建生成器实例
    generator = ProjectContextGenerator()
    
    try:
        # 生成上下文
        context = generator.generate_full_context()
        
        # 保存快照
        filename = generator.save_context_snapshot(context)
        
        print("=" * 50)
        print("✅ 项目上下文快照生成完成！")
        print(f"📄 文件位置: {filename}")
        print("💡 此文档可用于新会话的项目理解和开发衔接")
        
    except Exception as e:
        print(f"❌ 生成上下文快照时出错: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())