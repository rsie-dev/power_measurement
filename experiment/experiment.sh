#!/bin/bash
script_dir=`dirname $(readlink -f "$0")`
#echo script dir: $script_dir
activate=$script_dir/venv/bin/activate
. $activate
py=experiment.main
cd $script_dir
python -O -m $py "$@"
