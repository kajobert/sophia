#!/usr/bin/env python3
"""Helper to run SOPHIA autonomous sessions"""
import json
import sys
import time
import subprocess
from pathlib import Path
import requests

def post_instruction(instruction: str) -> dict:
    """Post instruction to SOPHIA API"""
    try:
        resp = requests.post(
            "http://127.0.0.1:8000/api/enqueue",
            json={"instruction": instruction},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def wait_for_completion(task_id: str, timeout: int = 300, poll_interval: int = 3) -> bool:
    """Wait for task completion by monitoring logs"""
    log_file = Path("logs/sophia.log")
    waited = 0
    print(f"Waiting up to {timeout}s for task {task_id} to complete...")
    
    while waited < timeout:
        if log_file.exists():
            # Read last 200 lines
            lines = subprocess.run(
                ["tail", "-200", str(log_file)],
                capture_output=True, text=True
            ).stdout
            
            # Check for completion markers
            if "Response ready" in lines or "Execution completed" in lines:
                print(f"Detected completion marker in logs (waited {waited}s)")
                return True
                
        time.sleep(poll_interval)
        waited += poll_interval
        
        if waited % 30 == 0:
            print(f"  ... still waiting ({waited}s)")
    
    print(f"Timeout after {waited}s")
    return False

def run_session(task_name: str, instructions_file: Path, step_timeout: int = 300):
    """Run autonomous session"""
    # Setup directories
    results_dir = Path("autotask_results")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    session_dir = results_dir / f"{task_name}_{timestamp}"
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # Load instructions
    with open(instructions_file) as f:
        instructions = json.load(f)
    
    # Save copy
    (session_dir / "instructions.json").write_text(json.dumps(instructions, indent=2))
    
    print(f"Starting autonomous session: {task_name} -> {len(instructions)} steps")
    print(f"Results will be saved to: {session_dir}")
    
    # Process each instruction
    for idx, step in enumerate(instructions, 1):
        step_id = step.get("id", f"step_{idx}")
        instruction = step["instruction"]
        
        print(f"\n--- Step {idx}/{len(instructions)}: {step_id}")
        print(f"Instruction: {instruction}")
        
        meta_file = session_dir / f"step_{idx}_meta.txt"
        with open(meta_file, "w") as f:
            f.write(f"Step {idx}/{len(instructions)}: {step_id}\n")
            f.write(f"Instruction: {instruction}\n\n")
        
        # Post instruction
        post_resp = post_instruction(instruction)
        print(f"Post response: {post_resp}")
        
        with open(meta_file, "a") as f:
            f.write(f"Post response: {json.dumps(post_resp)}\n")
        
        task_id = post_resp.get("task_id", "")
        if task_id:
            print(f"Task ID: {task_id}")
            with open(meta_file, "a") as f:
                f.write(f"Task ID: {task_id}\n")
        
        # Wait for completion
        completed = wait_for_completion(task_id if task_id else "", step_timeout)
        
        status = "completed" if completed else "timeout"
        print(f"Step {idx} {status}")
        
        with open(meta_file, "a") as f:
            f.write(f"Status: {status}\n")
        
        # Capture logs
        log_file = Path("logs/sophia.log")
        if log_file.exists():
            logs = subprocess.run(
                ["tail", "-200", str(log_file)],
                capture_output=True, text=True
            ).stdout
            (session_dir / f"step_{idx}_logs_tail.txt").write_text(logs)
            
            # Extract planner output
            planner_lines = [line for line in logs.split("\n") if "Raw LLM response received in planner" in line]
            if planner_lines:
                (session_dir / f"step_{idx}_planner.txt").write_text("\n".join(planner_lines))
            
            # Extract response
            response_lines = [line for line in logs.split("\n") if "Response ready" in line]
            if response_lines:
                (session_dir / f"step_{idx}_response_ready.txt").write_text("\n".join(response_lines))
        
        # Small cooldown
        time.sleep(2)
    
    print(f"\nAutonomous session complete. Results saved in {session_dir}")
    return session_dir

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <task-name> <instructions-file.json>")
        sys.exit(2)
    
    task_name = sys.argv[1]
    instructions_file = Path(sys.argv[2])
    
    if not instructions_file.exists():
        print(f"Error: {instructions_file} not found")
        sys.exit(1)
    
    run_session(task_name, instructions_file)
