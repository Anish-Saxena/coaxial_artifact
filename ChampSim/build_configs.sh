#!/bin/bash

while IFS= read -r line
do
	echo "Building " $line
	sleep 1
	./config.py CONFIGS/$line
	make -j8
done < $1
