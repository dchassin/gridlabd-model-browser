# GridLAB-D Model Browser

## Prerequisites
This tool uses GridLAB-D to view GLM files. If you are viewing only JSON file
you do not need to install GridLAB-D. See https://arras.energy/gridlabd for
instructions on how to download GridLAB-D.

## First time run

You should run this tool in a Python environment. To setup an environment,
run the following commands:

~~~
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pip --upgrade -r requirements.txt
~~~

## Running the viewer

To run the viewer activate a Python3 environment and run the app in Marimo.

~~~
source .venv/bin/activate
marimo run viewer.py
~~~

## Example file

You can download one of the https://arras.energy/gridlabd-models
using the `gridlabd model get` command, e.g.,
to download the IEEE 123 model, run

~~~
gridlabd model get IEEE/123
~~~
