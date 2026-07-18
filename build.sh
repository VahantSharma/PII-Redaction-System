#!/bin/bash
# Build script for Render deployment
set -e

pip install -r requirements.txt
python -m spacy download en_core_web_sm
