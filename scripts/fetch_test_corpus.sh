#!/usr/bin/env bash
# Fetch public-domain test corpora for the RAG benchmark (not committed to git).
set -e
mkdir -p data/test_corpus
echo "fetching Pride & Prejudice (Project Gutenberg, public domain)..."
curl -sL "https://www.gutenberg.org/files/1342/1342-0.txt" -o data/test_corpus/pride_and_prejudice.txt
echo "done: $(wc -w < data/test_corpus/pride_and_prejudice.txt) words"
