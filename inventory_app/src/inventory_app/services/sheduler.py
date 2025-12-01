from datetime import datetime, timedelta
import logging

# sheduler.py


# Configure logging
logging.basicConfig(level=logging.INFO)

class Scheduler:
    def __init__(self):
        self.tasks = []

    def add_task(self, task_name, run_at):
        task = {
            'name': task_name,
            'run_at': run_at
        }
        self.tasks.append(task)
        logging.info(f"Task '{task_name}' scheduled for {run_at}")

    def run_due_tasks(self):
        now = datetime.now()
        for task in self.tasks:
            if task['run_at'] <= now:
                self.execute_task(task)
                self.tasks.remove(task)

    def execute_task(self, task):
        logging.info(f"Executing task: {task['name']}")
        # Here you would add the actual task execution logic

# Example usage
if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.add_task("Inventory Check", datetime.now() + timedelta(seconds=10))
    while True:
        scheduler.run_due_tasks()