#!/bin/bash

## Compress files to be published with the release

# Main plugin files
name="PyViewDock"
contents="README.md \
          LICENSE \
          gui.ui \
          gui.py \
          io.py \
          __init__.py"
mkdir -p $name
for file in $contents; do
    cp $file $name/
done
zip ${name}.zip -r $name

# Examples
zip examples.zip -r examples
