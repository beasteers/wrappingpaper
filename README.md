# wrappingpaper

A collection of Python decorators and utilities to abstract away common/tedious Python patterns.

For example:
```python

@wp.contextdecorator
def doing_something(a, b):
    print(a)
    yield
    print(b)

# por que no los dos?

# you can do this
with doing_something(4, 5):
    print(1)

# as well as this
@doing_something(4, 5)
def something():
    print(1)
something()

```

#### Includes
 - [logging / error handling](#logging)
    - catch errors thrown in a function and redirect to logger
 - [context managers](#context-managers)
   - context managers that double as function wrappers
 - [iterable utils](#iterables)
 - [object property patterns](#properties)
 - [function default manipulation](#function-signature)
 - [misc](#misc)


## Install

```bash
pip install wrappingpaper
```

## Usage
```python
import wrappingpaper as wp
```

### Logging

```python
import logging
log = logging.getLogger(__name__)

# handle and log error

@wp.log_error_as_warning(log, default=dict)
def get_stats(x=None):
    if x is True:
        raise ValueError() # some error happens
    return {'a': 5, 'b': 6}

assert get_stats() == {'a': 5, 'b': 6}
assert get_stats(True) == {}
```

##### Roughly equivalent to:

```python
def get_stats(x=None):
    try:
        if x is True:
            raise ValueError() # some error happens
        return {'a': 5, 'b': 6}
    except ValueError as e:
        log.warning('Exception in get_stats: %s', e)
        return {}
```

### Context Managers

```python

@wp.contextdecorator
def doing_something(a, b):
    print(a)
    yield
    print(b)

# por que no los dos?

# you can do this
with doing_something(4, 5):
    print(1)

# as well as this
@doing_something(4, 5)
def something():
    print(1)
something()

```

##### Roughly equivalent to:

```python
import functools
from contextlib import contextmanager

@contextmanager
def doing_something(a, b):
    print(a)
    yield
    print(b)

def doing_something2(a, b):
    def outer(func):
        @functools.wraps(func)
        def inner(*a, **kw):
            with doing_something(a, b):
                return func(*a, **kw)
        return inner
    return outer

# used like:
with doing_something(4, 5):
    print(1)

@doing_something2(4, 5)
def something():
    print(1)
something()

```

### Properties

```python
import time

class SomeClass:
    @wp.cachedproperty
    def instance_prop(self):
        '''This is run once per object instance.'''
        return time.time()

    @wp.onceproperty
    def class_prop(self):
        '''This is run once. It is cached in the property
        object itself.'''
        return time.time()

    @wp.overrideable_property
    def overridable(self):
        return time.time()

    def __init__(self, overridable=None):
        if overridable: # override the property value
            # stores at self._overridable
            self.overridable = overridable
        # otherwise it just uses the property function like usual

a = SomeClass()
b = SomeClass()

assert a.instance_prop != b.instance_prop # prop runs once per object
assert a.class_prop == b.class_prop # prop runs only once
assert a.overridable != a.overridable # gets called twice, shouldn't be the same
a.overridable = 5
assert a.overridable == 5 # now the value is overridden

assert SomeClass(5).overridable == 5 # overriding inside class
```

### Function Signature

```python
# dynamic function defaults

@wp.configfunction
def asdf(a=5, b=6, c=7):
    return a + b + c

assert asdf() == 5+6+7 # normal behavior
asdf.update(a=1)
assert asdf() == 1+6+7 # updated default
assert asdf(3) == 3+6+7 # automatically resolves kwargs and posargs
asdf.clear()
assert asdf() == 5+6+7 # back to normal behavior

# filter out kwargs not in the signature (if **kw, it's a no-op).

@wp.filterkw
def asdf(a=5, b=6, c=7):
    return a + b + c

assert asdf(d=1234) == 5+6+7

```

## Iterables

```python

# make sure that a for loop doesn't go too fast.
# limit the time one iteration takes.

# limiting the number of iterations to 10.
# by default it loops infinitely.

for dt, time_asleep in wp.limit(wp.throttled(1), 10):
    print('Iteration took {}s. Had to sleep for {}s.'.format(dt, time_asleep))
    print('-'*10)


# check the first n items in an iterable, without removing them.

it = iter(range(6))
items, it = wp.pre_check_iter(it, 3)
assert items == [0, 1, 2]
assert list(it) == [0, 1, 2, 3, 4, 5, 6]


# repeat and chain iterables infinitely

import random

def get_numbers():
    return [random.random() for _ in range(10)]

numbers = wp.run_iter_forever(get_numbers)
# repeat get_numbers() and chain iterable outputs together
all_numbers = list(wp.limit(numbers, 100))
assert all(isinstance(x, float) for x in all_numbers)

def get_numbers():
    if random.random() > 0.8: # make random breaks
        return # returns empty
    return [random.random() for _ in range(10)]

numbers = wp.run_iter_forever(get_numbers, none_if_empty=True)
# this SHOULD contain sporadic None's at a multiple of 10
all_numbers = list(wp.limit(numbers, 5000))
assert None in all_numbers
```

## Misc

```python
import random

# retry a function if an exception is raised

@wp.retry_on_failure(10)
def asdf():
    x = random.random()
    if x < 0.5:
        raise ValueError
    return x

# will either return a number that is definitely > 0.5
# or every number in the first 10 tries were below 0.5
try:
    assert asdf() > 0.5
except ValueError:
    print("Couldn't get a number :/")


# ignore error

with wp.ignore():
    a, b = 5, 0
    c = a / b # throws divide by zero
    a = 10 # never run
assert a == 5


# A wrappable alternative to `while True:`

for _ in wp.infinite():
    print('this is gonna be a while...')

```