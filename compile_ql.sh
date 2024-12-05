#/usr/bin/zsh
# Adaptation of scripts of FireFingers21 and zeitlings
# https://www.alfredforum.com/topic/22139-shipping-swift-code-in-workflows/

readonly exe_file="${alfred_workflow_data}/ql"
readonly source_file="./ql-source/ql.swift"

# Compile ql if possible and needed
if [[ ! -f "${exe_file}" || "$(date -r "${source_file}" +%s)" -gt "$(date -r "${exe_file}" +%s)" ]] \
    && [[ "$(which swiftc)" =~ "/swiftc" ]]; then
   mkdir -p "${alfred_workflow_data}"
   xcrun swiftc -O "${source_file}" -o "${exe_file}" &
fi

