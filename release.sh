#!/bin/bash

## Compress files to be published with the release

# Main plug-in files
name="PyViewDock"
cp_contents="README.md \
             LICENSE"
for file in $cp_contents; do
    cp $file $name/
done
rm -rf $name/__pycache__
zip ${name}.zip -r $name
for file in $cp_contents; do
    rm $name/$file
done

# Examples
zip examples.zip -r examples
