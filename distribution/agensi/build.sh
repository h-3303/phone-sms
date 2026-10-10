#!/bin/sh
# Build the Agensi upload: a ZIP whose top-level folder is `phone-sms/` with SKILL.md and LICENSE.
# Only the MIT skill goes in; the GPL server never enters the ZIP (it is installed from PyPI).
set -eu
cd "$(dirname "$0")/../.."
mkdir -p dist/agensi
rm -f dist/agensi/phone-sms.zip
(cd plugin/skills && zip -q -X -r ../../dist/agensi/phone-sms.zip phone-sms -x '*/.*')
unzip -l dist/agensi/phone-sms.zip
