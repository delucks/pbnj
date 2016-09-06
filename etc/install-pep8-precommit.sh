cat << DOG > .git/hooks/pre-commit
#!/usr/bin/env sh
if hash flake8; then
  flake8 pbnj/
fi
DOG
