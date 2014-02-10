import signal
import sys
import subprocess

# Since process.wait() does not have a timeout
# argument, we do this hack with signal to get a timeout
class TimeoutException:
    pass
def timeout_handler(signum, frame):
    raise TimeoutException
signal.signal(signal.SIGALRM, timeout_handler)

def fail_with(s):
    """
    Prints the error message and exits with return code 1
    """
    print "[FAILURE] %s" % s
    sys.exit(1)

def launch_command(command, timeout, logfile):
    """
    Execs `command` in a subprocess, and returns the
    stdout as a list of strings. Will fail if the
    command takes longer than timeout
    """
    out = open(logfile, "w")
    proc = subprocess.Popen(command,
                            shell=True,
                            stdout=out,
                            stderr=subprocess.STDOUT)
    try:
        signal.alarm(timeout)
        proc.wait()
    except TimeoutException:
        out.close()
        proc.kill()
        fail_with("operation took too long (> %d seconds)" % timeout)

    out.close()
    signal.alarm(0) # reset alarm
    lines = None
    with open(logfile, "r") as f:
        lines = f.readlines()
    return lines

def get_output_lines(lines):
    """
    Finds all the lines between:
    OS/161 kernel: command...
    ...
    Operation took .... seconds
    """
    # Remove new line chars
    lines = map(lambda l: l.strip(), lines);

    # Find the line that starts with "OS/161 kernel"
    start_line = filter(lambda (n,l): l.startswith("OS/161 kernel"),
                        enumerate(lines))[0]
    start_index = start_line[0]

    # Find the line that starts with "Operation took"
    end_line_candidates = filter(lambda (n,l): l.startswith("Operation took"),
                                 enumerate(lines))
    if len(end_line_candidates) != 1:
        fail_with("Could not find 'Operation took' string => synching synch probs not done?")
    end_index = end_line_candidates[0][0]

    # Keep only the lines between start and end
    lines = lines[start_index + 1:end_index]
    return lines
