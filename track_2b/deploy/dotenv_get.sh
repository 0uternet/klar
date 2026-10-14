#!/bin/sh
# Print the value of KEY from a dotenv file (last assignment wins), or nothing.
# Handles "export KEY=...", "quoted" / 'quoted' values, trailing " # comments" and CRLF.
# usage: dotenv_get.sh FILE KEY
f=${1:?usage: dotenv_get.sh FILE KEY}
k=${2:?usage: dotenv_get.sh FILE KEY}
[ -f "$f" ] || exit 0
sed -n "s/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}$k[[:space:]]*=[[:space:]]*//p" "$f" \
  | tail -n 1 \
  | tr -d '\r' \
  | sed -e 's/^"\([^"]*\)".*$/\1/' -e t \
        -e "s/^'\([^']*\)'.*\$/\1/" -e t \
        -e 's/[[:space:]]#.*$//' \
        -e 's/[[:space:]]*$//'
