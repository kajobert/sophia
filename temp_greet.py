import sys
sys.path.insert(0, './sandbox/custom_tools/')
from pozdrav import pozdravit

greeting = pozdravit('Světe')
print(greeting)