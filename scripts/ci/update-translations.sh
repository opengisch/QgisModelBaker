#!/bin/bash
./scripts/update-strings.sh en
./scripts/push-transifex-translations.sh
./scripts/pull-transifex-translations.sh
./scripts/compile-strings.sh projectgenerator/i18n/*.ts
