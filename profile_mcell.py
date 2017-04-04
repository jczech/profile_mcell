#!/usr/bin/env python

import subprocess
import random
import time
import os
import yaml
import argparse
import shutil
import collections
import pandas
import seaborn


def get_mcell_vers(mcell_bin):
    proc = subprocess.Popen([mcell_bin], stdout=subprocess.PIPE)
    output = proc.stdout.readlines()
    first_line = output[0].decode('UTF-8').split()
    vers = first_line[1]
    commit = first_line[3]
    return (vers, commit)


def parse_test():
    mdl_name = ""
    categories = []
    command_line_opts = []
    with open("./test_description.toml", 'r') as toml_f:
        for line in toml_f.readlines():
            words = line.split()
            if words and words[0].startswith("mdlfiles"):
                mdl_name = words[2][2:-2]
            elif words and words[0].startswith("keywords"):
                # Uhhh... evals are bad. Change this.
                categories = eval(line.split("=")[1])
            elif words and words[0].startswith("commandlineOpts"):
                command_line_opts = eval(line.split("=")[1])
    return (mdl_name, categories, command_line_opts)


def run_mcell(mcell_bin, mdl_name, command_line_opts):
    seed = random.randint(1, 2147483647)
    command = [mcell_bin, '-seed', '%d' % seed, mdl_name]
    command.extend(command_line_opts)
    start = time.time()
    subprocess.call(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    end = time.time()
    elapsed_time = end-start
    return elapsed_time


def build_nutmeg():
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/nutmeg'])
    os.chdir("nutmeg")
    subprocess.call(['git', 'pull'])
    os.chdir("tests")
    os.chdir("../..")


def build_mcell(num_bins, step, branch):
    bin_dict = collections.OrderedDict()
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/mcell'])
    os.chdir("mcell")
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'checkout', branch])
    build_dir = "build"
    # shutil.rmtree(build_dir, ignore_errors=True)
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    os.chdir(build_dir)
    for i in range(num_bins):
        # Only build if we need to. Use existing versions if it exists.
        proc = subprocess.Popen(
            ["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
        git_hash = proc.stdout.read().decode('UTF-8')
        new_mcell_name = "mcell_%s" % git_hash[:8]
        if not os.path.exists(new_mcell_name):
            subprocess.call(["make", "clean"])
            subprocess.call(["cmake", ".."])
            subprocess.call(["make"])
            shutil.copy("mcell", new_mcell_name)
        mcell_bin = os.path.join(os.getcwd(), new_mcell_name)
        bin_dict[mcell_bin] = git_hash[:-1]
        subprocess.call(["git", "checkout", "HEAD~%d" % step])
    os.chdir("../..")

    return bin_dict


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="How to profile MCell using nutmeg tests:")
    parser.add_argument(
        "-n", "--num", default=1,
        help="number of versions of MCell to run from git repo")
    parser.add_argument(
        "-s", "--step",  default=1,
        help="number of steps between MCell versions")
    parser.add_argument(
        "-c", "--category", help="category for tests")
    parser.add_argument(
        "-b", "--branch", help="git branch", default="master")
    return parser.parse_args()


def main():
    args = setup_argparser()
    category = args.category
    num_bins = int(args.num)
    step = int(args.step)
    branch = args.branch

    build_nutmeg()
    # This is how many versions of MCell we want to test (starting with master
    # and going back)
    bin_dict = build_mcell(num_bins, step, branch)
    # bin_dict = {'/home/jacob/profile_mcell/mcell/build/mcell_1': 'd5a8e9031b315c94b332f8323e70648b38a97865', '/home/jacob/profile_mcell/mcell/build/mcell_0': '1130752c89233230cc56379e1d2dc2af819bb7bc'}

    os.chdir("nutmeg/tests")
    dirs = os.listdir(os.getcwd())
    dirs.sort()
    run_info_list = []
    for mcell_bin in bin_dict:
        mdl_times = {}
        run_info = {}
        for dirn in dirs:
            if not os.path.isdir(dirn):
                continue
            os.chdir(dirn)
            mdl_name, categories, command_line_opts = parse_test()
            mdl_dir_fname = "{0}/{1}".format(dirn, mdl_name)
            if category in categories:
                elapsed_time = run_mcell(mcell_bin, mdl_name, command_line_opts)
                mdl_times[mdl_dir_fname] = elapsed_time
            os.chdir("..")
        total_time = sum([mdl_times[k] for k in mdl_times])
        run_info['mcell_bin'] = bin_dict[mcell_bin]
        run_info['mdl_times'] = mdl_times
        run_info['total_time'] = total_time
        run_info_list.append(run_info)
    with open("mdl_times.yml", 'w') as mdl_times_f:
        yml_dump = yaml.dump(
            run_info_list, allow_unicode=True, default_flow_style=False)
        mdl_times_f.write(yml_dump)
    times_df = pandas.DataFrame(
        data=[(i['mcell_bin'][:8], i['total_time']) for i in run_info_list],
        columns=["binary", "time"])
    times_df = times_df.set_index("binary")
    ax = times_df.plot(
        title="Running Times for MCell Binaries", legend=False, kind="bar",
        rot=0)
    ax.set_ylabel("Time (s)")
    ax.set_xlabel("Git SHA ID")
    ax.get_figure().savefig("output.png")


if __name__ == "__main__":
    main()
