#!/usr/bin/env bash
set -e


echo "Clear up \"dist/\"..."
mkdir -p dist
rm -rf dist
mkdir -p dist
echo "done"
echo -
echo -

echo "Re-build front..."
./scripts_build/build_front.sh
echo "done"
echo -
echo -

echo "Re-build front..."
./scripts_build/build_bring_front_manifest_to_back.sh
echo "done"
echo -
echo -

echo "Re-build back..."
./scripts_build/build_back.sh
echo "done"
echo -
echo -
