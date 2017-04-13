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
    skip = True
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
            elif (words and words[0].startswith("testType") and
                  words[2].startswith('"CHECK_SUCCESS"')):
                skip = False
    return (mdl_name, categories, command_line_opts, skip)


def run_mcell(mcell_bin, mdl_name, command_line_opts):
    seed = random.randint(1, 2147483647)
    command = [mcell_bin, '-seed', '%d' % seed, mdl_name]
    command.extend(command_line_opts)
    print(" ".join(command))
    start = time.time()
    proc = subprocess.Popen(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    err_str = proc.stderr.read().decode('UTF-8')
    end = time.time()
    err_list = err_str.split("\n")
    if [e for e in err_list if e.startswith("Error") or e.startswith("Fatal")]:
        elapsed_time = None
    else:
        elapsed_time = end-start
    return elapsed_time


def build_nutmeg():
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/nutmeg'])
    os.chdir("nutmeg")
    subprocess.call(['git', 'pull'])
    os.chdir("tests")
    os.chdir("../..")


def list_nutmeg_categories():
    os.chdir("nutmeg")
    command = ["./nutmeg", "-L"]
    subprocess.Popen(command)
    os.chdir("..")


def build_mcell(num_bins, step, branch):
    bin_dict = collections.OrderedDict()
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/mcell'])
    os.chdir("mcell")
    subprocess.call(['git', 'pull'])
    subprocess.call(['git', 'checkout', branch])
    build_dir = "build"
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


def plot_times(run_info_list, categories):
    total_run_list = []
    for run in run_info_list:
        binary = run['mcell_bin'][:8]
        curr_run = [binary]
        for key in run['total_time']:
            curr_run.append(run['total_time'][key])
        total_run_list.append(curr_run)

    column_list = ['binary']
    column_list.extend(categories)
    times_df = pandas.DataFrame(data=total_run_list, columns=column_list)

    times_df = times_df.set_index("binary")
    ax = times_df.plot(
        title="Running Times for MCell Binaries", kind="bar",
        rot=0)
    ax.set_ylabel("Time (s)")
    ax.set_xlabel("Git SHA ID")
    ax.get_figure().savefig("output.png")


def clean_builds():
    os.chdir("mcell")
    build_dir = "build"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
    os.chdir("..")


def run_tests(bin_dict, dirs, selected_categories):
    run_info_list = []
    for mcell_bin in bin_dict:
        mdl_times = {}
        mdl_total_times = {}
        for category in selected_categories:
            mdl_total_times[category] = {}
            mdl_times[category] = {}
        run_info = {}
        for dirn in dirs:
            if not os.path.isdir(dirn):
                continue
            os.chdir(dirn)
            mdl_name, categories, command_line_opts, skip = parse_test()
            if skip:
                os.chdir("..")
                continue
            mdl_dir_fname = "{0}/{1}".format(dirn, mdl_name)
            for category in selected_categories:
                if category in categories:
                    elapsed_time = run_mcell(
                        mcell_bin, mdl_name, command_line_opts)
                    mdl_times[category][mdl_dir_fname] = elapsed_time
            os.chdir("..")
        for category in selected_categories:
            total_time_list = [
                mdl_times[category][k] for k in mdl_times[category]]
            if None in total_time_list:
                print("Commit %s has failures." % bin_dict[mcell_bin])
                break
            else:
                total_time = sum(total_time_list)
            mdl_total_times[category] = total_time
        run_info['mcell_bin'] = bin_dict[mcell_bin]
        run_info['mdl_times'] = mdl_times
        run_info['total_time'] = mdl_total_times
        run_info_list.append(run_info)
    return run_info_list


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
        "-c", "--categories", action="append", help="category for tests")
    parser.add_argument(
        "-b", "--branch", help="git branch", default="master")
    parser.add_argument(
        "-C", "--clean", action="store_true", help="clean old MCell builds")
    parser.add_argument(
        "-l", "--list_categories", action="store_true",
        help="list nutmeg categories")
    return parser.parse_args()


def main():
    args = setup_argparser()
    categories = args.categories
    num_bins = int(args.num)
    step = int(args.step)
    branch = args.branch

    if args.clean:
        clean_builds()

    if args.list_categories:
        list_nutmeg_categories()
    else:
        build_nutmeg()
        # This is how many versions of MCell we want to test (starting with
        # HEAD and going back)
        bin_dict = build_mcell(num_bins, step, branch)

        os.chdir("nutmeg/tests")
        dirs = os.listdir(os.getcwd())
        dirs.sort()
        run_info_list = run_tests(bin_dict, dirs, categories)
        os.chdir("../..")
        with open("mdl_times.yml", 'w') as mdl_times_f:
            yml_dump = yaml.dump(
                run_info_list, allow_unicode=True, default_flow_style=False)
            mdl_times_f.write(yml_dump)
        plot_times(run_info_list, categories)


if __name__ == "__main__":
    main()
