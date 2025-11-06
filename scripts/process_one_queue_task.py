# scripts/process_one_queue_task.py
import asyncio
import sys
from core.simple_persistent_queue import SimplePersistentQueue
from core.kernel import Kernel

async def main():
    q = SimplePersistentQueue(db_path='.data/tasks.sqlite')
    task = q.dequeue_and_lock()
    if not task:
        print('No pending task found')
        return 0
    tid = task['id']
    payload = task['payload']
    instruction = payload.get('instruction')
    print(f'Processing task id={tid} instruction snippet: {str(instruction)[:120]}')

    kernel = Kernel(use_event_driven=False, offline_mode=False)
    await kernel.initialize()
    try:
        await kernel.consciousness_loop(single_run_input=instruction)
        q.mark_done(tid)
        print(f'Task {tid} processed and marked done')
        return 0
    except Exception as e:
        print(f'Error processing task {tid}: {e}', file=sys.stderr)
        q.mark_failed(tid, reason=str(e))
        return 2

if __name__ == '__main__':
    exit(asyncio.run(main()))
