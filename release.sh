#!/bin/bash

## Compress files to be published with the release

pyviewdock_path=$(dirname $(readlink -f ${BASH_SOURCE[0]}))
cd $pyviewdock_path

# release folder
rm -rf "release"
mkdir "release"

# Main plug-in files
name="PyViewDock"
cp_contents="README.md \
             LICENSE"
for file in $cp_contents; do
    cp $file $name/
done
rm -rf $name/__pycache__
zip "release"/${name}.zip -r $name
for file in $cp_contents; do
    rm $name/$file
done

# Examples
zip "release"/examples.zip -r examples

cd -
