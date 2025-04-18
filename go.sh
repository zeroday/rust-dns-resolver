#!/bin/bash

# DNS resolver commands for detected patterns

# Pattern: sunpass.com-XXXX.win
./target/release/rust-dns-resolver --pattern 'sunpass\.com-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp"

# Pattern: txtag.org-XXX.win
./target/release/rust-dns-resolver --pattern 'txtag\.org-[a-z]{3}\.win' -c 100 -H 50 --status-path "/front/checkIp"

# Pattern: txtag.org-XXXX.win
./target/release/rust-dns-resolver --pattern 'txtag\.org-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" 