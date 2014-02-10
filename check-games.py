import argparse
from common import *

SP2_NUM_MAPPINGS = 128

class Record:
    KATNISS = "katniss"
    PEETA = "peeta"

    def __init__(self, who, capitol, district, deleted):
        self.who = who
        self.capitol = capitol
        self.district = district
        self.deleted = deleted

def gen_records(lines, num_mappings):
    records = []
    for l in lines:
        l = l.strip()
        if not l.startswith("{") or not l.endswith("}"):
            failwith("must be enclosed in {}")
        words = map(lambda w: w.strip(), l[1:-1].split(","))
        expected = ["who", "capitol", "district", "deleted"]
        if len(words) != 4:
            failwith("format {who: W, capitol: C, district: D, deleted: N}, got: %s" % l)
        values = []
        for (i, word) in enumerate(words):
            fields = map(lambda w: w.strip(), word.split(":"))
            if len(fields) != 2 and fields[0] != expected[i]:
                failwith("format {who: W, capitol: C, district: D, deleted: N}, got: %s" % l)
            values.append(fields[1])
        records.append(Record(values[0], int(values[1]), int(values[2]), int(values[3])))
    return records

def check_deleted_nums(records, num_mappings):
    dels = [record.deleted for record in records]
    dels_sorted = sorted(dels)
    expected = range(1, SP2_NUM_MAPPINGS + 1)
    if expected != list(dels_sorted):
        fail_with("deleted numbers must all appear once 1 to %d, got: %s"
                  % (SP2_NUM_MAPPINGS, dels))

def check_mappings(records, num_mappings):
    capitols = {}
    districts = {}
    for record in records:
        capitol = record.capitol
        district = record.district
        if capitol in capitols:
            fail_with("already deleted capitol: %d" % capitol)
        if district in districts:
            fail_with("already deleted district: %d" % district)
        capitols[capitol] = district
        districts[district] = capitol

    if len(capitols) != num_mappings:
        fail_with("len(capitols) == %d, expected: %d" % (len(capitols), num_mappings))
    if len(districts) != num_mappings:
        fail_with("len(districts) == %d, expected: %d" % (len(districts), num_mappings))

    for capitol in capitols:
        district = capitols[capitol]
        if districts[district] != capitol:
            fail_with("mismatch: capitols[%d] = %d, districts[%d] = %d"
                      % (capitol, capitols[capitols], district, districts[district]))
    for district in districts:
        capitol = districts[district]
        if capitols[capitol] != district:
            fail_with("mismatch: capitols[%d] = %d, districts[%d] = %d"
                      % (capitol, capitols[capitols], district, districts[district]))

def check_who(records):
    for record in records:
        if record.who != Record.KATNISS and record.who != Record.PEETA:
            fail_with("unknown who: %s" % record.who)

SP2_LOG_FILE = "sp2.out"
SP2_TIMEOUT = 20 # seconds
SP2_ITERATIONS = 5

parser = argparse.ArgumentParser("check script for cows")
parser.add_argument("--timeout",
                    type=int,
                    help="timeout (seconds), default: %d seconds" % SP2_TIMEOUT,
                    default=SP2_TIMEOUT,
                    dest="timeout")
parser.add_argument("--iterations",
                    type=int,
                    help="num iterations to run, default: %d" % SP2_ITERATIONS,
                    default=SP2_ITERATIONS,
                    dest="iterations")
parser.add_argument("--logfile",
                    type=str,
                    help="log file prefix, default: %s" % SP2_LOG_FILE,
                    default=SP2_LOG_FILE,
                    dest="logfile")

args = vars(parser.parse_args())
timeout = args["timeout"]
iterations = args["iterations"]
logfile_base = args["logfile"]
command = "sys161 kernel 'sp2; q'"

for i in range(iterations):
    logfile = "%s.%d" % (logfile_base,i)

    print "Running iteration %d, logfile: %s ..." % (i, logfile)
    lines = launch_command(command, timeout, logfile)
    write_lines(lines, logfile)
    lines = get_output_lines(lines)
    records = gen_records(lines, SP2_NUM_MAPPINGS)
    check_deleted_nums(records, SP2_NUM_MAPPINGS)
    check_mappings(records, SP2_NUM_MAPPINGS)
    check_who(records)
    print "[SUCCESS] All checks passed!"
