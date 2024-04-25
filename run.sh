#!/bin/sh
pushd $(dirname -- "$0")
. .venv/bin/activate
python main.py
