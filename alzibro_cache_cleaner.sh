#!/bin/zsh
#
cache_folder="${alfred_workflow_cache}"
cache_basename="alzibro_cache"
cache_pid_basename="cache_script.pid"
last_zip_basename="last_cached_zipfile"
cache_timeout="${alzibro_cache_timeout}"
cache_file="${cache_folder}/${cache_basename}" 
cache_pid_file="${cache_folder}/${cache_pid_basename}"
cache_last_zipfile="${cache_folder}/${last_zip_basename}"

# Put the pid in cache_script.pid file
echo $$ > "$cache_pid_file"

# Set the clock 
i=$cache_timeout
running=true

# Renew timeout on signal
function handle_signal() {
  i=$cache_timeout 
}
trap "handle_signal" USR1

# Main loop -- wait
while $running; do
  sleep 10
  ((i -= 10))
  if ((i <= 0)); then
    running=false
  fi
done

# Clear the cache
rm -f $cache_file
rm -f $cache_pid_file
rm -f $cache_last_zipfile

