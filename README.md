# profile_mcell

Requirements
--------------------------------------------------------------------
You need the following Python libraries:

  * pyyaml
  * pandas
  * matplotlib

You also need the following packages (to build MCell):

  * cmake
  * bison
  * flex
  * build-essential
  * clang

Overview
--------------------------------------------------------------------

A tool to profile MCell's performance between selected commits

Currently, this will only work in Linux (and probably OSX). The testing is
pretty basic. It will build selected commits of MCell and test them against
specific nutmeg tests.

To get help, run this:

    ./profile_mcell.py -h

Here's an example of how you would use it:

    ./profile_mcell.py -c "dynamic geometry" -n 5 -s 5 -b dynamic_meshes

This would run the test against the "dynamic geometry" category of tests in
nutmeg. It would test 5 different MCell commits starting with the HEAD and
going backwards in the repo history by increments of 5, and the test would
operate on the dynamic_meshes branch.

Here are a few more examples:

    ./profile_mcell.py -n 2 -c leak -c az -c rat_nmj -b master -b dynamic_meshes
    ./profile_mcell.py -l   # list the possible categories
    ./profile_mcell.py -p   # plot based off of existing data
    ./profile_mcell.py -C   # clear intermediate files

The category flag (-c) will accept any nutmeg category, i.e. the following:

 - reactions
 - checkpoint
 - argparse
 - error messages
 - leak
 - regression
 - releases
 - parser
 - periodic
 - surface_classes
 - warning messages

Additionally, it will accept the following non-nutmeg categories:

 - az
 - rat_nmj
 - lv

The branch flag (-b) will accept any MCell branch:

 - binary_reaction_output
 - coverity_scan
 - dynamic_meshes
 - dynamic_meshes_pymcell
 - master
 - mcellNeuronECC
 - mcell_neuron
 - neumann_boundaries
 - nfsim_diffusion
 - nfsim_merge
 - nfsim_merge_2
 - periodic_BC
 - periodic_BC_ng
 - pipe_interface
 - print_command_line
 - smp
 - smp_new
 - surface_clamp
