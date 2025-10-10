import os
import sys
import subprocess

def run_cli_with_env(module_name, env_vars, input_bytes=b"\n", timeout=5):
    """
    Run a CLI module with environment variables and return the result.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(os.path.dirname(__file__))
    env.update(env_vars)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "run", "-m", module_name],
            input=input_bytes, capture_output=True, env=env, timeout=timeout, check=False
        )
        return result
    except subprocess.TimeoutExpired:
        return None
