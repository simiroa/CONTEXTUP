"""
ContextUp Feature Test Suite
=============================

Automated testing of GUI features with log analysis and error detection.

Usage:
    python feature_test.py              # Test all features
    python feature_test.py manager      # Test specific feature
    python feature_test.py --quick      # Quick mode (skip slow features)

Output:
    - Console report with pass/fail status
    - Log analysis for errors and warnings
    - Screenshot capture (optional)
"""

import subprocess
import sys
import time
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # ContextUp/
SRC_DIR = PROJECT_ROOT / "src"
LOGS_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = SCRIPT_DIR / "test_reports"
REPORT_DIR.mkdir(exist_ok=True)

# Feature definitions: (id, module_path, description, test_type)
# test_type: 'import' = just test import, 'launch' = launch GUI, 'function' = run function
FEATURES = [
    # Core
    ("core.menu", "core.menu", "Menu Dispatcher", "import"),
    ("core.config", "core.config", "Config Loader", "import"),
    ("core.registry", "core.registry", "Registry Manager", "import"),
    
    # Manager
    ("manager.ui.app", "manager.ui.app", "Manager GUI", "import"),
    ("manager.mgr_core.config", "manager.mgr_core.config", "Config Manager", "import"),
    ("manager.mgr_core.process", "manager.mgr_core.process", "Tray Process Manager", "import"),
    
    # Features - Audio
    ("features.audio.tools", "features.audio.tools", "Audio Tools", "import"),
    ("features.audio.convert_gui", "features.audio.convert_gui", "Audio Convert GUI", "import"),
    
    # Features - Video
    ("features.video.tools", "features.video.tools", "Video Tools", "import"),
    ("features.video.convert_gui", "features.video.convert_gui", "Video Convert GUI", "import"),
    ("features.video.downloader_gui", "features.video.downloader_gui", "Video Downloader GUI", "import"),
    
    # Features - Image
    ("features.image.convert_gui", "features.image.convert_gui", "Image Convert GUI", "import"),
    
    # Features - AI
    ("features.ai.tools", "features.ai.tools", "AI Tools", "import"),
    ("features.ai.marigold_gui", "features.ai.marigold_gui", "Marigold PBR GUI", "import"),
    ("features.ai.frame_interp", "features.ai.frame_interp", "Frame Interpolation", "import"),
    
    # Features - Mesh
    ("features.mesh.blender", "features.mesh.blender", "Blender Tools", "import"),
    ("features.mesh.mayo", "features.mesh.mayo", "Mayo Tools", "import"),
    
    # Features - System
    ("features.system.tools", "features.system.tools", "System Tools", "import"),
    ("features.system.rename", "features.system.rename", "Rename Tools", "import"),
    
    # Tray
    ("tray.agent", "tray.agent", "Tray Agent", "import"),
    
    # Utils
    ("utils.external_tools", "utils.external_tools", "External Tools", "import"),
    ("utils.batch_runner", "utils.batch_runner", "Batch Runner", "import"),
    ("utils.progress_gui", "utils.progress_gui", "Progress GUI", "import"),
]


class TestResult:
    def __init__(self, feature_id: str, description: str):
        self.feature_id = feature_id
        self.description = description
        self.passed = False
        self.error = None
        self.warnings = []
        self.duration = 0.0
    
    def __str__(self):
        status = "[PASS]" if self.passed else "[FAIL]"
        msg = f"{status} {self.description}"
        if self.error:
            msg += f" - {self.error}"
        return msg


class LogAnalyzer:
    """Analyze log files for errors and warnings."""
    
    ERROR_PATTERNS = [
        r"Error:",
        r"ERROR",
        r"Exception:",
        r"Traceback",
        r"Failed to",
        r"not found",
        r"ModuleNotFoundError",
        r"ImportError",
        r"FileNotFoundError",
    ]
    
    WARNING_PATTERNS = [
        r"Warning:",
        r"WARNING",
        r"Could not",
        r"deprecated",
    ]
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = logs_dir
    
    def get_recent_logs(self, minutes: int = 5) -> Dict[str, str]:
        """Get log content from recently modified files."""
        logs = {}
        cutoff = time.time() - (minutes * 60)
        
        for log_file in self.logs_dir.glob("*.log"):
            try:
                if log_file.stat().st_mtime > cutoff:
                    logs[log_file.name] = log_file.read_text(encoding='utf-8', errors='replace')
            except:
                pass
        return logs
    
    def find_errors(self, content: str) -> List[str]:
        """Find error lines in log content."""
        errors = []
        for line in content.split('\n'):
            for pattern in self.ERROR_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(line.strip())
                    break
        return errors[:10]  # Limit to first 10
    
    def find_warnings(self, content: str) -> List[str]:
        """Find warning lines in log content."""
        warnings = []
        for line in content.split('\n'):
            for pattern in self.WARNING_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    warnings.append(line.strip())
                    break
        return warnings[:10]
    
    def analyze(self) -> Dict:
        """Analyze recent logs and return summary."""
        logs = self.get_recent_logs()
        all_errors = []
        all_warnings = []
        
        for name, content in logs.items():
            errors = self.find_errors(content)
            warnings = self.find_warnings(content)
            if errors:
                all_errors.extend([(name, e) for e in errors])
            if warnings:
                all_warnings.extend([(name, w) for w in warnings])
        
        return {
            "log_files": list(logs.keys()),
            "errors": all_errors,
            "warnings": all_warnings,
        }


class FeatureTester:
    """Test ContextUp features for functionality."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.python = sys.executable
        self.results: List[TestResult] = []
        self.log_analyzer = LogAnalyzer(project_root / "logs")
    
    def test_import(self, feature_id: str, module_path: str, description: str) -> TestResult:
        """Test if a module can be imported without errors."""
        result = TestResult(feature_id, description)
        start = time.time()
        
        try:
            # Use forward slashes for cross-platform compatibility
            src_dir_str = str(self.src_dir).replace('\\', '/')
            cmd = [
                self.python, "-c",
                f"import sys; sys.path.insert(0, '{src_dir_str}'); import {module_path}; print('OK')"
            ]
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root)
            )
            
            if proc.returncode == 0 and "OK" in proc.stdout:
                result.passed = True
            else:
                result.error = proc.stderr.strip()[:200] if proc.stderr else "Unknown error"
                
        except subprocess.TimeoutExpired:
            result.error = "Timeout (30s)"
        except Exception as e:
            result.error = str(e)[:200]
        
        result.duration = time.time() - start
        return result
    
    def run_all_tests(self, filter_pattern: str = None) -> List[TestResult]:
        """Run all feature tests."""
        print("=" * 60)
        print("ContextUp Feature Test Suite")
        print("=" * 60)
        print(f"Project: {self.project_root}")
        print(f"Python: {self.python}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        for feature_id, module_path, description, test_type in FEATURES:
            # Apply filter if specified
            if filter_pattern and filter_pattern.lower() not in feature_id.lower():
                continue
            
            print(f"Testing: {description}...", end=" ", flush=True)
            
            if test_type == "import":
                result = self.test_import(feature_id, module_path, description)
            else:
                # Other test types can be added here
                result = self.test_import(feature_id, module_path, description)
            
            self.results.append(result)
            
            status = "[PASS]" if result.passed else "[FAIL]"
            print(f"{status} ({result.duration:.2f}s)")
            
            if result.error:
                # Show truncated error
                err_lines = result.error.split('\n')
                for line in err_lines[:3]:
                    print(f"    {line}")
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a summary report."""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        
        # Log analysis
        log_analysis = self.log_analyzer.analyze()
        
        report = []
        report.append("")
        report.append("=" * 60)
        report.append("TEST SUMMARY")
        report.append("=" * 60)
        report.append(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        report.append(f"Success Rate: {passed/total*100:.1f}%" if total > 0 else "N/A")
        report.append("")
        
        if failed > 0:
            report.append("FAILED TESTS:")
            for r in self.results:
                if not r.passed:
                    report.append(f"  - {r.feature_id}: {r.error[:100]}")
            report.append("")
        
        if log_analysis["errors"]:
            report.append("LOG ERRORS (recent):")
            for log_name, error in log_analysis["errors"][:5]:
                report.append(f"  [{log_name}] {error[:80]}")
            report.append("")
        
        if log_analysis["warnings"]:
            report.append("LOG WARNINGS (recent):")
            for log_name, warning in log_analysis["warnings"][:5]:
                report.append(f"  [{log_name}] {warning[:80]}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self) -> Path:
        """Save detailed report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORT_DIR / f"test_report_{timestamp}.json"
        
        data = {
            "timestamp": timestamp,
            "project_root": str(self.project_root),
            "python": self.python,
            "results": [
                {
                    "id": r.feature_id,
                    "description": r.description,
                    "passed": r.passed,
                    "error": r.error,
                    "duration": r.duration
                }
                for r in self.results
            ],
            "log_analysis": self.log_analyzer.analyze()
        }
        
        report_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return report_file


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ContextUp Feature Test Suite")
    parser.add_argument("filter", nargs="?", help="Filter tests by name pattern")
    parser.add_argument("--quick", action="store_true", help="Quick mode")
    parser.add_argument("--save", action="store_true", help="Save JSON report")
    
    args = parser.parse_args()
    
    tester = FeatureTester(PROJECT_ROOT)
    tester.run_all_tests(args.filter)
    
    print(tester.generate_report())
    
    if args.save:
        report_path = tester.save_report()
        print(f"Report saved: {report_path}")
    
    # Exit code based on failures
    failures = sum(1 for r in tester.results if not r.passed)
    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
