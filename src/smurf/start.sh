#!/usr/bin/env bash

filename="$1"
name="${filename%.*}"

rm -rf $name
mkdir $name

tar -xzvf $1 -C $name

cd $name

smurf cache --notify .

./run.sh
cd ..

mv $filename $name
