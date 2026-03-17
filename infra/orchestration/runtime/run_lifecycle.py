from infra.orchestration.runtime.run_controller import RunController
from infra.orchestration.runtime.run_queue import RunQueue


class RunLifecycleEngine:
    def __init__(self):
        self.queue = RunQueue()
        self.controller = RunController()

    def enqueue_run(self, run_request):
        self.queue.enqueue(run_request)

    def process_next_run(self):
        if self.queue.is_empty():
            return None

        run_request = self.queue.dequeue()

        return self.controller.start_run(run_request)

    def process_all_runs(self):
        results = []

        while not self.queue.is_empty():
            result = self.process_next_run()
            results.append(result)

        return results
