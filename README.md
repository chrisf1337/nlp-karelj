## Todos/fixmes
- [x] Implement pick action
- [x] Implement drop action
- [ ] Implement conditional
- [ ] Implement while

## Setup
Consider using [virtualenv](https://virtualenv.pypa.io/en/latest/) to contain your dependencies. If
you don't use virtualenv, you will probably need to install dependencies with `sudo pip` instead of
`pip`. Clone this repository, then make sure you have the proper dependencies installed. See
https://github.com/dasmith/stanford-corenlp-python to see what you need for the Stanford CoreNLP
wrapper, but if you run
```
pip install pexpect unidecode
cd stanford_corenlp_python
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2014-08-27.zip
unzip stanford-corenlp-full-2014-08-27.zip
```

you should be able to start the server with
```
cd stanford_corenlp_python
python corenlp.py
```

You will need to install some more dependencies with `pip`:
```
pip install enum34 nltk subprocess32 colorama
```

To run all the tests in the `tests` dir, run `python run_tests.py`. To run specific test numbers,
run `python run_tests.py [test numbers]`. To see the output of a certain parse, run `python
parser.py test-n.txt`.

## Project structure
- `parser.py` uses the dependency output from CoreNLP to try to construct Action objects that
  describe what actions the robot should take. The `parse()` function takes in a sentence string,
  obtains the dependency parse output from the CoreNLP server, and returns a list of Action
  objects.
- `codegen.py` contains one function, `generate_code()`, which takes in a list of actions from
  `parse()` and a `.template` file and writes the generated Java source to an output file.
- `run_tests.py` sequentially runs the tests in the `tests` directory and indicates the success or
  failure of each test. See the section below for more information.
- `dependency.py` contains some utils that I wrote to extract useful information from the output of
  the dependency parser.
- `log.py` contains some colored print wrappers for more convenient logging.

## Test structure
`run_tests.py` expects the following files to exist in the `tests` directory:
- `KarelJRobot.jar`, the jar file defining the Karel J Robot Java objects
- `TestRobot.template`, a text file that looks mostly like a Java source file, but with `{{ }}`
  tags, which are replaced by `codegen.py` with relevant strings like the test number and the
  injected code for each test

`run_tests.py` also expects one of each of the following files to exist in the `tests` directory
for each test number `n`:
- `test-n.txt`, a text file containing an English language sentence that is converted to Karel J
  Robot Java code
- `start-n.kwld`, a text file containing a description of the starting state of the world. See the
  [Karel J Robot simulator page](https://csis.pace.edu/~bergin/KarelJava2ed/karelexperimental.html)
  for a description of how this file is formatted. Note that streets run from east to west
  (horizontal) and avenues run from north to south (vertical), so the street number of a beeper or
  robot is its y coordinate and the avenue number is its x coordinate. The `kwld` format requires
  that the street number of a beeper or robot be specified before its avenue number, so effectively
  coordinates in the `kwld` file are in the format `(y, x)` (confusing!). We also currently assume
  that the starting position of the robot is at street 2, avenue 2, facing east, with 0 beepers.
- `end-n.kwld`, a description of the expected end state of the world that should result from
  running the actions specified in `test-n.txt`. The format of this file is the exact same as that
  of `start-n.kwld`, with one extra line that describes the expected end position and direction of
  the robot, in the format `robot %d %d %s`, where the first two `%d` are the street and avenue
  number of the robot and the last `%s` is the cardinal direction of the robot (capitalized)

For each test `n`, `run_tests.py` will create the following files:
- `TestRobotn.java`, the generated Java code from `codegen.py`
- `TestRobotn.class`, the compiled Java class file from `TestRobotn.java`
- `test-n.log`, a text file containing some useful information printed out by `parser.py` and
  `TestRobotn` during the process of parsing and running the Java class file
- `end-n-test.kwld`, a description of the end state of the world after running `TestRobotn`. The
  format of this file is exactly the same as that of `end-n.kwld`.

Currently, test outputs are evaluated on an all-or-nothing scale: if the state of the world
described in `end-n-test.kwld` matches the state described in `end-n.kwld`, the test is awarded 1
point; otherwise, it is awarded 0 points.

## Known issues
- English sentences should be relatively "well-formed" (i.e., more or less conforming to
  well-defined Karel commands/conditions). I'm not sure how well it can handle confusing cases.
- Verbs are not stemmed when searching in the `verb_mapping` dict.
- Error handling is pretty iffy.
