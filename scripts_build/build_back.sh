#!/usr/bin/env bash
set -e

echo "Init python"
source .venv/bin/activate
echo "done"
echo -
echo -

echo "Update program version"
./scripts_build/build_back_generate_progver.sh
echo "done"
echo -
echo -

echo "Re-build htmler..."
./scripts_build/build_back_component_html.sh
echo "done"
echo -
echo -

echo "Produce \"webserve_bundle.py\""
echo "Calling pinliner..."
# if [ ! -f "src_dev_build/lib/pinliner/pinliner/pinliner.py" ]; then
#   # TODO: confirm is having --remote fine? I think it is. It's something like apt update, it is normal to run this occasionally. I don't see an issue
#   git submodule update --init --recursive --remote
# fi
# comment: please delete .pyc files before every call of the webserve_bundle - this is implemented in my fork of the pinliner
# python src_dev_build/lib/pinliner/pinliner/pinliner.py src_backend -o dist/webserve_bundle.py --verbose
python "src_dev_build/lib/pinliner/pinliner/pinliner.py" src_backend -o dist/webserve_bundle.py
echo "done"
echo "Patching webserve_bundle.py..."
echo "# ..." >> "dist/webserve_bundle.py"
echo "# print('within webserve_bundle')" >> "dist/webserve_bundle.py"
# no need for this, the root package is loaded automatically
# echo "# import webserve_bundle" >> "dist/webserve_bundle.py"
echo "from src_backend import launcher" >> "dist/webserve_bundle.py"
echo "launcher.main()" >> "dist/webserve_bundle.py"
echo "# print('out of webserve_bundle')" >> "dist/webserve_bundle.py"
echo "done"
echo -
echo -


echo "Bring \"static\" files to ./static/"
mkdir -p ./dist/static
rsync -av --exclude='*.py' src_backend/endpoints/lib/htmltmpl/compiled/ ./dist/static/
echo "done"
echo -
echo -

python dist/webserve_bundle.py --program done
deactivate
