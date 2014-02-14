import argparse
from common import *
import re

SP1_LYRICS = set([
    "I threw a wish in the well",
    "Don't ask me, I'll never tell",
    "I looked to you as it fell",
    "And now you're in my way",
    "I'd trade my soul for a wish",
    "Pennies and dimes for a kiss",
    "I wasn't looking for this",
    "But now you're in my way",
    "Your stare was holdin'",
    "Ripped jeans, skin was showin'",
    "Hot night, wind was blowin'",
    "Where do you think you're going, baby?",
    "Hey, I just met you",
    "And this is crazy",
    "But here's my number",
    "So call me, maybe!",
])

def gen_parent_babies_table(lines, num_babies):
    """
    Return mappings
    babies: baby num -> (line, lyric) for that baby
    parent: baby num -> when it was congratulated
    """
    babies = dict(((i,[]) for i in range(num_babies)))
    parent = dict(((i,[]) for i in range(num_babies)))

    # Parse each line
    # Formats
    #    "Baby N Cow: lyric"
    #    "Parent Cow: Congratulations Baby N!"
    for (lnum, l) in enumerate(lines):
        # find the location of ":"
        colon_i = l.find(":")
        if colon_i == -1:
            fail_with("Improper output string: %s" % l)
        prefix = l[:colon_i]
        suffix = l[colon_i + 1:]

        # remove extra white space and split the string
        prefix_words = map(lambda s: s.strip(), re.sub(r'\s{2,}', ' ', prefix).split())

        # "Baby N Cow: lyric"
        if prefix_words[0] == 'Baby':
            if len(prefix_words) != 3 or prefix_words[2] != "Cow":
                fail_with("expected format 'Baby N Cow: lyric', got: %s" % l)
            try:
                baby_num = int(prefix_words[1])
            except ValueError as e:
                fail_with("error when parsing baby num, line: %s, error: %s", l, str(e))
            if baby_num < 0 or baby_num >= num_babies:
                fail_with("baby num out of range: %s", l)
            lyric = suffix.strip()
            babies[baby_num].append((lnum, lyric))

        # "Parent Cow: Congratulations Baby N!"
        elif prefix_words[0] == 'Parent':
            if len(prefix_words) != 2 or prefix_words[1] != "Cow":
                fail_with("expected format 'Parent Cow: Congratulations Baby N!', got: %s" % l)
            suffix = suffix.strip()
            if suffix[-1] != "!":
                fail_with("expected format 'Parent Cow: Congratulations Baby N!', got: %s" % l)
            suffix_words = map(lambda s: s.strip(), re.sub(r'\s{2,}', ' ', suffix[:-1]).split())
            if suffix_words[0] != "Congratulations" or suffix_words[1] != "Baby":
                fail_with("expected format 'Parent Cow: Congratulations Baby N!', got: %s" % l)
            try:
                baby_num = int(suffix_words[-1])
            except ValueError as e:
                fail_with("error when parsing baby num, line: %s, error: %s" % (l, str(e)))
            if baby_num < 0 or baby_num >= num_babies:
                fail_with("baby num out of range: %s", l)
            parent[baby_num].append(lnum)

        # If anything else, fail
        else:
            fail_with("line does not start with Baby or Parent: %s" % l)
    return parent, babies

def check_baby_lyrics(babies):
    """
    check that all the lyrics are in LYRICS
    """
    for baby_num in babies:
        for (_,lyric) in babies[baby_num]:
            if lyric not in SP1_LYRICS:
                fail_with("baby %d sang unknown lyric: %s" % (baby_num, lyric))

def check_parent_congratulate(babies, parent):
    """
    make sure each baby is congratulated exactly once, and
    that it was congratulated after its last lyric
    """
    # find the last line each baby sings, or -1 if no lines
    last_lines = {}
    for baby_num in babies:
        lnums = [lnum for (lnum, _) in babies[baby_num]]
        lnums.append(-1)
        last_lines[baby_num] = max(lnums)

    # make sure each baby is congratulated exactly once AFTER it's last line
    for baby_num in parent:
        if len(parent[baby_num]) != 1:
            fail_with("baby %d must be congratulated exactly once" % baby_num)
        if parent[baby_num] <= last_lines[baby_num]:
            fail_with("baby %d was congratulated before it finished" % baby_num)

SP1_NUM_BABIES = 10
SP1_LOG_FILE = "sp1.out"
SP1_TIMEOUT = 10 # seconds
SP1_ITERATIONS = 5

parser = argparse.ArgumentParser("check script for cows")
parser.add_argument("--timeout",
                    type=int,
                    help="timeout (seconds), default: %d seconds" % SP1_TIMEOUT,
                    default=SP1_TIMEOUT,
                    dest="timeout")
parser.add_argument("--babies",
                    type=int,
                    help="num babies, default: %d" % SP1_NUM_BABIES,
                    default=SP1_NUM_BABIES,
                    dest="num_babies")
parser.add_argument("--iterations",
                    type=int,
                    help="num iterations to run, default: %d" % SP1_ITERATIONS,
                    default=SP1_ITERATIONS,
                    dest="iterations")
parser.add_argument("--logfile",
                    type=str,
                    help="log file prefix, default: %s" % SP1_LOG_FILE,
                    default=SP1_LOG_FILE,
                    dest="logfile")

args = vars(parser.parse_args())
timeout = args["timeout"]
num_babies = args["num_babies"]
iterations = args["iterations"]
logfile_base = args["logfile"]
command = "sys161 kernel 'sp1 %d; q'" % num_babies

for i in range(iterations):
    logfile = "%s.%d" % (logfile_base,i)
    print "Running iteration %d, logfile: %s ..." % (i, logfile)
    lines = launch_command(command, timeout, logfile)
    lines = get_output_lines(lines)
    parent, babies = gen_parent_babies_table(lines, num_babies)
    check_baby_lyrics(babies)
    check_parent_congratulate(babies, parent)
    print "[SUCCESS] All checks passed!"
