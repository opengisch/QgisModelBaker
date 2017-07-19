#!/bin/bash
if test "$TRAVIS_SECURE_ENV_VARS" = "true" -a "$TRAVIS_BRANCH" = "master";
then
  echo -e "[https://www.transifex.com]\nhostname = https://www.transifex.com\nusername = api\npassword = $TRANSIFEX_API_TOKEN\ntoken =\n" > ~/.transifexrc

  ./scripts/update-strings.sh en
  ./scripts/push-transifex-translations.sh
  ./scripts/pull-transifex-translations.sh
  ./scripts/compile-strings.sh i18n/*.ts
else
  echo "Translation not done. We only use transifex if TRAVIS_BRANCH is master (currently ${TRAVIS_BRANCH}) and TRAVIS_SECURE_ENV_VARS is true (currently ${TRAVIS_SECURE_ENV_VARS})."
fi
