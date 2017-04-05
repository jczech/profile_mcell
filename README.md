# profile_mcell
A tool to profile MCell's performance between selected commits

Currently, this will only work in Linux (and probably OSX). The testing is pretty basic. It will build selected commits of MCell and test them against specific nutmeg tests.

Here's an example of how you would use it:

    python profile_mcell.py -c "dynamic geometry" -n 5 -s 5 -b dynamic_meshes

This would run the test against the "dynamic geometry" category of tests in nutmeg. It would test 5 different MCell commits starting with the HEAD and going backwards in the repo history by increments of 5, and the test would operate on the dynamic_meshes branch.
