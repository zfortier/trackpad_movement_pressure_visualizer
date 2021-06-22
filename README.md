# Mouse Pressure Plotter
Used to visualize the movement and pressure of trackpad events captured using
`libinput record`


# Usage
first, record some output using `libinput`:

```
$ libinput record /dev/input/event15 > data
```
replace the device path with whatever your trackpad is assigned. Then input
your test movements and stop recording with `crtrl-c`.

Now run the script:
```
./mouse_data_parser.py data
```

it should generate a 3d plot that shows the trajectory and pressure recorded
for the trackpad during the test input.


# Requirements
  - A sane linux installation
  - Python 3
  - libinput
  - numpy
  - pandas
  - sympy (not actually used but could allow for some interesting analysis)
  - matplotlib (pyplot)
  - mpl\_toolkits (mplot3d)

