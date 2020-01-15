#!/usr/bin/env python3
import sys, os
import unittest

# add the tests directory to python path
# to make imports work properly across platforms
def repo_abspath():
    # add src directory to path for imports
    this_files_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(this_files_dir)
    return repo_dir

sys.path = sys.path[:1] + [os.path.join(repo_abspath(),"src")] + sys.path[1:]

# import unit test cases
from test_import import *

def main():
    unittest.main()

if __name__ == "__main__":
    main()
