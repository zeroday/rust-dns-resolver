#!/bin/bash

# DNS resolver commands for detected patterns - running in parallel

# Pattern: sunpass.com-XXXX.win
./target/release/rust-dns-resolver --pattern 'sunpass\.com-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: txtag.org-XXX.win
./target/release/rust-dns-resolver --pattern 'txtag\.org-[a-z]{3}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: txtag.org-XXXX.win
./target/release/rust-dns-resolver --pattern 'txtag\.org-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: mass.gov-XXXX.win
./target/release/rust-dns-resolver --pattern 'mass\.gov-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: michigan.gov-eXXXXX.win
./target/release/rust-dns-resolver --pattern 'michigan\.gov-e[a-z]{5}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: ncquickpass.com-XXXX.win
./target/release/rust-dns-resolver --pattern 'ncquickpass\.com-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: ohioturnpike.org-XXXX.win
./target/release/rust-dns-resolver --pattern 'ohioturnpike\.org-[a-z]{4}\.win' -c 100 -H 50 --status-path "/front/checkIp" &

# Pattern: paturnpike.com-XXX.cc
./target/release/rust-dns-resolver --pattern 'paturnpike\.com-[a-z]{3}\.cc' -c 100 -H 50 --status-path "/front/checkIp" &

# Wait for all background processes to complete
wait 