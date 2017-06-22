#!/bin/bash
./scripts/update-strings.sh en
./scripts/push-transifex-translations.sh
./scripts/pull-transifex-translations.sh
./scripts/compile-strings.sh i18n/*.ts
mkdir projectgenerator/i18n
mv i18n/*.qm projectgenerator/i18n
