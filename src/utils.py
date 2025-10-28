from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
package_path = project_root / "python-package" / "employee_events"

event_color = "\033[96m"
complete_color = "\033[92m"
color_end = "\033[0m"
