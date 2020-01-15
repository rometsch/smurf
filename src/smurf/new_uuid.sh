#!/usr/bin/env bash
# Give the simulation a new uuid
# This is stored as a file with the uuid as filename in meta/uuid/{uuid}
[[ "$#" -eq 1 ]] && BASEDIR="$(realpath $1)" || BASEDIR="$PWD"
UUID="$(uuidgen)"
if [[ -e "$BASEDIR/job" ]];then
        METADIR="$BASEDIR/job"
elif [[ -e "$BASEDIR/meta" ]]; then
        METADIR="$BASEDIR/meta"
else
        >&2 echo "Invalid simulation dir. Does not contain 'job' dir."
        exit 1
fi
if [[ -e "$METADIR/uuid.txt" ]]; then
        echo "$UUID" > "$METADIR/uuid.txt"
fi
mkdir -p "$METADIR/uuid"
for F in $(ls $METADIR/uuid); do
        rm "$METADIR/uuid/$F"
done
touch "$METADIR/uuid/$UUID"
echo "$UUID"
