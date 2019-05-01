#!/bin/bash

user="xf08id"

find_processes() {
    echo "$(ps -ef | grep '/ipython' | grep -v grep | awk '{ if ($1 == "'$user'") {print} }')"
}

raw_processes=$(find_processes)

echo "Found IPython processes for $user:"
echo "==================================="
echo "$raw_processes"

pids=$(echo $(echo "$raw_processes" | awk '{print $2}'))

if [ ! -z "$pids" ]; then
    echo -e "\nPIDs to kill: $pids"
    read -p "Continue? (y/[N]): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1
    echo "Killing $pids..."
    kill $pids
    echo -e "\nProcesses after killing:"
    echo "========================"
    echo "$(find_processes)"
fi
