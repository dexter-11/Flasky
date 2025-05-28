#!/bin/bash

set -euo pipefail
IFS=$'\n\t'

# --- Config ---
baseDir="/home/lab/BugBounty/recon"
HTTP_PORTS="80,443,8080,8443,9000,9080"
DIRSEARCH_EXT="php,html,js,json,txt,xml,zip,sql,asp,aspx,jsp,action,conf,config,bak,log,old,inc"

# File Names
ROOTS_FILE="_roots.txt"
DOMAINS_FILE="_domains.txt"
IPS_FILE="_ips.txt"
OUTOFSCOPE_FILE="outofscope.txt"
RESOLVED_DOMAINS_FILE="resolveddomains.txt"
LIVE_WEBSERVERS_FILE="livewebservers.txt"
OPEN_PORTS_FILE="openports.txt"

# --- Colors and Icons ---
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"
CHECK="${GREEN}[✓]${NC}"
CROSS="${RED}[✗]${NC}"
RUNNING="${YELLOW}[⏳]${NC}"
DONE="${GREEN}[🎉]${NC}"

# --- Main Script ---
echo -e "${YELLOW}"
echo "=============================="
echo "  Recon Automation Script     "
echo "=============================="
echo -e "${NC}"

if [[ ! -d "$baseDir" ]]; then
    echo -e "${RED}[-] Base directory '$baseDir' not found.${NC}"
    exit 1
fi

process_dir() {
    local dir="$1"
    local dirName
    dirName=$(basename "$dir")

    if [[ "$dirName" == ".ignoredirs" ]]; then
        echo -e "${YELLOW}[-] Skipping ignored dir: $dirName${NC}"
        return
    fi

    # Check if already done
    if [[ -f "$dir/.recon_done" ]]; then
        echo -e "${CHECK} Already completed $dirName, skipping."
        return
    fi

    echo -e "${RUNNING} Processing $dirName"
    pushd "$dir" > /dev/null || { echo -e "${CROSS} Failed to enter $dir"; return; }

    # Check required files
    if [[ ! -f "$ROOTS_FILE" || ! -f "$DOMAINS_FILE" || ! -f "$IPS_FILE" ]]; then
        echo -e "${CROSS} Missing required files in $dirName. Skipping."
        popd > /dev/null
        return
    fi

    # 2. Subfinder + dnsx
    if subfinder -dL "$ROOTS_FILE" -silent 2>/dev/null | dnsx -silent -resp-only > temp_subfinder_dnsx.txt; then
        echo -e "${CHECK} $dirName: Subdomain Enum"
    else
        echo -e "${CROSS} $dirName: Subdomain Enum"
    fi

    # 2a. Gungnir
    if gungnir -dL "$ROOTS_FILE" -silent 2>/dev/null > temp_gungnir.txt; then
        echo -e "${CHECK} $dirName: Certificate Transparency (CT)"
    else
        echo -e "${CROSS} $dirName: Certificate Transparency (CT)"
    fi

    # 3. dnsx on domains.txt
    if dnsx -l "$DOMAINS_FILE" -silent -resp-only > temp_dnsx_domains.txt; then
        echo -e "${CHECK} $dirName: DNS Resolution"
    else
        echo -e "${CROSS} $dirName: DNS Resolution"
    fi

    # Merge all results
    cat temp_subfinder_dnsx.txt temp_gungnir.txt temp_dnsx_domains.txt 2>/dev/null | sort -u > "$RESOLVED_DOMAINS_FILE"
    rm -f temp_subfinder_dnsx.txt temp_gungnir.txt temp_dnsx_domains.txt

    # Remove out-of-scope domains
    if [[ -f "$OUTOFSCOPE_FILE" ]]; then
        if grep -vxFf "$OUTOFSCOPE_FILE" "$RESOLVED_DOMAINS_FILE" > temp; then
            mv temp "$RESOLVED_DOMAINS_FILE"
            echo -e "${CHECK} $dirName: Out-of-Scope Cleanup"
        else
            echo -e "${CROSS} $dirName: Out-of-Scope Cleanup"
        fi
    fi

    # 4. httpx - live servers
    if httpx -l "$RESOLVED_DOMAINS_FILE" -p "$HTTP_PORTS" -silent -o "$LIVE_WEBSERVERS_FILE"; then
        echo -e "${CHECK} $dirName: Live Web Servers"
    else
        echo -e "${CROSS} $dirName: Live Web Servers"
    fi

    # 5. smap open ports
    cat "$RESOLVED_DOMAINS_FILE" "$IPS_FILE" | sort -u > targets_for_smap.txt
    if smap -iL targets_for_smap.txt -o "$OPEN_PORTS_FILE"; then
        echo -e "${CHECK} $dirName: Open Ports Scan"
    else
        echo -e "${CROSS} $dirName: Open Ports Scan"
        rm -f targets_for_smap.txt
        popd > /dev/null
        return
    fi
    rm -f targets_for_smap.txt

    # 6. dirsearch
    mkdir -p out/dirsearch/
    if cat "$LIVE_WEBSERVERS_FILE" | xargs -P 10 -I % bash -c '
        dirsearch -u "%" -e "'"$DIRSEARCH_EXT"'" -x 404 -t 20 --recursion "404" --max-recursion-depth 3 --exclude-subdirs images/,css/ \
        -o out/dirsearch/$(echo "%" | sed "s|https\?://||g" | tr "/:" "_").txt
    '; then
        echo -e "${CHECK} $dirName: Dirsearch"
    else
        echo -e "${CROSS} $dirName: Dirsearch"
    fi

    # 7. Crawl all URLs using gau and store output
    mkdir -p jsfiles/
    if cat "$LIVE_WEBSERVERS_FILE" | gau --subs | sort -u > gau.out; then
        echo -e "${CHECK} $dirName: URL Crawl (gau)"
    else
        echo -e "${CROSS} $dirName: URL Crawl (gau)"
    fi

    # Extract all .js files from gau.out
    if grep -iE "\.js(\?|$)" gau.out | sort -u > jsfiles/all_jsfiles.txt; then
        echo -e "${CHECK} $dirName: JS File Extraction"
    else
        echo -e "${CROSS} $dirName: JS File Extraction"
    fi

    # 8. Separate out "chunk" js
    mkdir -p jsmap_chunks/
    if grep -i "chunk" jsfiles/all_jsfiles.txt > jsmap_chunks/chunk_files.txt; then
        echo -e "${CHECK} $dirName: Chunk JS Separation"
    else
        echo -e "${CROSS} $dirName: Chunk JS Separation"
    fi


    # Done - create marker
    touch ".recon_done"

    echo -e "${DONE} Completed $dirName"
    popd > /dev/null
}

export -f process_dir
export baseDir ROOTS_FILE DOMAINS_FILE IPS_FILE OUTOFSCOPE_FILE RESOLVED_DOMAINS_FILE LIVE_WEBSERVERS_FILE OPEN_PORTS_FILE
export GREEN RED YELLOW BLUE NC CHECK CROSS RUNNING DONE HTTP_PORTS DIRSEARCH_EXT

# Run in parallel
find "$baseDir" -mindepth 1 -maxdepth 1 -type d | parallel -j 4 process_dir {}

# --- Cleanup ---
echo -e "${GREEN}\n[+] All processing done. Resetting resume markers...${NC}"
find "$baseDir" -name ".recon_done" -delete

echo -e "${GREEN}\n🎯 Recon completed for all targets. Ready for next run!${NC}"
