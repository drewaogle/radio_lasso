#!/bin/bash

if [ -d "$1" ]; then
    out="$(realpath -m $2/$1)"
    echo "mac: DIR  $1 $2 => $out"
    echo mkdir -p "$out/"
    mkdir -p "$out/"
else
    out="$(realpath $2/$1)"
    echo "mac: FILE  $1 $2 => $out"
    cp "$1" "$out"
fi
