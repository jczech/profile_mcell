import subprocess
import random
import time
import os
import yaml
import argparse
import shutil


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


def build_mcell():
    subprocess.call(['git', 'clone', 'https://github.com/mcellteam/mcell'])
    os.chdir("mcell")
    subprocess.call(['git', 'pull'])
    build_dir = "build"
    shutil.rmtree(build_dir, ignore_errors=True)
    os.mkdir(build_dir)
    os.chdir(build_dir)
    subprocess.call(["cmake", ".."])
    subprocess.call(["make"])
    mcell_dir = os.getcwd()
    mcell_bin = os.path.join(mcell_dir, "mcell")
    os.chdir("../..")

    return mcell_bin


def setup_argparser():
    parser = argparse.ArgumentParser(
        description="How to profile MCell using nutmeg tests:")
    parser.add_argument("category", help="category for tests")
    return parser.parse_args()


def main():
    args = setup_argparser()
    category = args.category

    build_nutmeg()
    mcell_bin = build_mcell()

    mdl_times = {}
    os.chdir("nutmeg/tests")
    dirs = os.listdir(os.getcwd())
    dirs.sort()
    mcell_vers, commit = get_mcell_vers(mcell_bin)
    all_stuff = {'mcell_vers': mcell_vers, 'commit': commit}
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
    all_stuff['mdl_times'] = mdl_times
    all_stuff['total_time'] = total_time
    with open("mdl_times.yml", 'w') as mdl_times_f:
        mdl_times_f.write(yaml.dump(all_stuff, default_flow_style=False))


if __name__ == "__main__":
    main()
