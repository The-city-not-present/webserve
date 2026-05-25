#!/usr/bin/env bash
set -e


echo "Calling git describe..."
mkdir -p src_backend/GENERATED
echo "" > src_backend/GENERATED/__init__.py
echo '"""Generated with make build from git describe; must include _VERSION = ...something"""' > src_backend/GENERATED/_VERSION.py
echo "# updated" > src_backend/GENERATED/_VERSION.py
python -c 'from datetime import datetime; print(f"# {datetime.now()}")' >> src_backend/GENERATED/_VERSION.py
echo "_VERSION = '''" >> src_backend/GENERATED/_VERSION.py
git describe >> src_backend/GENERATED/_VERSION.py
echo "'''" >> src_backend/GENERATED/_VERSION.py
echo "done"
echo -
echo -
