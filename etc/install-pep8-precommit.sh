cat << DOG > .git/hooks/pre-commit
#!/usr/bin/env bash
function cmd_exists() {
  eval "which \$1" >/dev/null 2>&1
}
if cmd_exists pep8
then
  pep8 irc.py
fi
DOG
