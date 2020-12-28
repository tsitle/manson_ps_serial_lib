# Manson Lab Power Supply Python Library for Serial Programming

## Prerequisites

### Installing Python3:

- Debian/Ubuntu

	```
	$ sudo apt-get install python3 python3-pip
	```
- macOS (tested on macOS 10.14 Mojave)  
	Install [HomeBrew](https://brew.sh/index_de):

	```
	$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	```

	Install Python3:

	```
	$ brew install python3
	```

### Installing pySerial:

see [pySerial Docs](https://pyserial.readthedocs.io/en/latest/pyserial.html#installation)

- Debian/Ubuntu

	```
	$ sudo apt-get install python3-serial
	```
- macOS

	```
	$ python3 -m pip install pyserial
	```

## Compatible Power Supply models

| Manson   | Specs             | B&K Precision (OEM) | Multicomp (OEM) | Peaktech (OEM) | Voltcraft (OEM) |
|:--------:|:-----------------:|:-------------------:|:---------------:|:--------------:|:---------------:|
| HCS-3100 | 1..18V 0..10A     |                     |                 |                | PPS-11810       |
| HCS-3102 | 1..36V 0..5A      |                     |                 |                | PPS-11360       |
| HCS-3104 | 1..60V 0..2.5A    |                     |                 |                | PPS-11603       |
| HCS-3150 | 1..18V 0..15A     |                     |                 |                |                 |
| HCS-3200 | 1..18V 0..20A     | 1688B               |                 |                | PPS-13610       |
| HCS-3202 | 1..36V 0..10A     | 1687B               |                 |                | PPS-16005       |
| HCS-3204 | 1..60V 0..5A      | 1685B               |                 |                | PPS-11815       |
| HCS-3300 | 1..16V 0..30A     |                     |                 |                | DPPS-16-30      |
| HCS-3302 | 1..32V 0..15A     |                     |                 |                | DPPS-32-15      |
| HCS-3304 | 1..60V 0..8A      |                     |                 |                | DPPS-60-8       |
| HCS-3400 | 1..16V 0..40A     |                     |                 | 1565           | DPPS-16-40      |
| HCS-3402 | 1..32V 0..20A     |                     |                 | 1575           | DPPS-32-20      |
| HCS-3404 | 1..60V 0..10A     |                     |                 |                | DPPS-60-10      |
| HCS-3600 | 1..16V 0..60A     | 1900B               |                 | 1570           | DPPS-16-60      |
| HCS-3602 | 1..32V 0..30A     | 1901B               |                 | 1580           | DPPS-32-30      |
| HCS-3604 | 1..60V 0..15A     | 1902B               |                 | 1585           | DPPS-60-15      |
| NTP-6521 | 1..20V 0.25..5A   |                     | MP710079        |                |                 |
| NTP-6531 | 1..36V 0.25..3A   |                     | MP710080        |                |                 |
| NTP-6561 | 1..60V 0.25..1.6A |                     | MP710081        |                |                 |
| NTP-6621 | 1..20V 0.25..5A   |                     |                 |                |                 |
| NTP-6631 | 1..36V 0.25..3A   |                     |                 |                |                 |
| NTP-6661 | 1..60V 0.25..1.6A |                     |                 |                |                 |
| SSP-8080 | 0..16V 0..5A      |                     |                 |                |                 |
| SSP-8160 | 0..42V 0..10A     |                     |                 |                | CPPS-160-42     |
| SSP-8162 | 0..84V 0..5A      |                     |                 |                | CPPS-160-84     |
| SSP-8320 | 0..42V 0..20A     |                     |                 |                | CPPS-320-42     |
| SSP-8322 | 0..84V 0..10A     |                     |                 |                | CPPS-320-84     |
| SSP-9081 | 0.5..36V 0..5A    |                     | MP710083        |                |                 |

Please note that this library has only been tested with a Manson HCS-3202 power supply so far.  
Support for all other models was added only by using the vendor's command references and specs.

## Running the Test Suite using an emulated Instrument

```
$ python3 run_test_emulated_instruments.py
```

To see the available options:

```
$ python3 run_test_emulated_instruments.py --help
```

## Running the Test Suite using a real Instrument

```
$ python3 run_test_real_instrument.py COMPORT

e.g.
$ python3 run_test_real_instrument.py /dev/ttyUSB0
```

To see the available COMPORTs:

```
$ python3 run_test_real_instrument.py list
```

To see the available options:

```
$ python3 run_test_real_instrument.py --help
```

## Running the Example Script using a real Instrument

```
$ python3 run_example_real_instrument.py COMPORT

e.g.
$ python3 run_example_real_instrument.py /dev/ttyUSB0
```

To see the available COMPORTs:

```
$ python3 run_example_real_instrument.py list
```

To see the available options:

```
$ python3 run_example_real_instrument.py --help
```
