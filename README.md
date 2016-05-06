## Setup
Clone this repository, then make sure you have the proper dependencies installed. See
https://github.com/dasmith/stanford-corenlp-python to see what you need for the Stanford CoreNLP
wrapper, but if you run
```
sudo pip install pexpect unidecode
```

you should be able to start the server with
```
cd stanford_corenlp_python
python corenlp.py
```

`poc.py` is some proof of concept code with some ideas I'm toying with. Right now I'm trying to
figure out how to turn the Stanford CoreNLP dependency parser output (which is sort of hit or miss,
take a look at my comments or play around with the code to see what the output is) into something
usable. `dependency.py` contains some utils that I wrote to extract useful information from the
output of the dependency parser.
