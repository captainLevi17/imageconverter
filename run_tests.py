"""Script to run tests and save output to a file."""
import sys
import io
from contextlib import redirect_stdout, redirect_stderr

def run_tests():
    """Run tests and return the output."""
    # Redirect stdout and stderr to capture all output
    stdout = io.StringIO()
    stderr = io.StringIO()
    
    with redirect_stdout(stdout), redirect_stderr(stderr):
        # Import and run pytest
        import pytest
        exit_code = pytest.main(['tests/test_detailed.py', '-v', '-s'])
    
    # Get the output
    output = stdout.getvalue() + '\n' + stderr.getvalue()
    return exit_code, output

if __name__ == "__main__":
    print("Running tests...")
    exit_code, output = run_tests()
    
    # Save output to file
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Tests completed with exit code: {exit_code}")
    print(f"Output saved to test_output.txt")
