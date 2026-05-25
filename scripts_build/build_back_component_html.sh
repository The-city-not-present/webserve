#!/usr/bin/env bash
set -e


echo "Changin path to src_backend/endpoints/lib/htmltmpl and calling build..."
pushd src_backend/endpoints/lib/htmltmpl
if [ -f compiled/html_bundle.py ]; then
  rm -rf compiled/html_bundle.py
fi
make init
make build-only-static
rm .env
popd
echo "done"
echo -
echo -
