from pathlib import Path


class DumpLogger:
    def __init__(self):
        self.log_dict: dict[str, dict[str, Path]] = {'calculations': {}, 'workflows': {}}

    def update_calculations(self, new_calculations: dict[str, Path]):
        """Update the log with new calculations."""
        self.log_dict['calculations'].update(new_calculations)

    def update_workflows(self, new_workflows: dict[str, Path]):
        """Update the log with new workflows."""
        self.log_dict['workflows'].update(new_workflows)

    def get_logs(self):
        """Retrieve the current state of the log."""
        return self.log_dict
