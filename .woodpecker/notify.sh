#!/usr/bin/env bash

#slixsend -j anon.azylum.org -p foo -m -t kaliko@conf.azylum.org "${CI_REPO}: ${CI_PIPELINE_URL}"
env

if [ "${CI_PREV_PIPELINE_STATUS}" != "failure" ] && [ "${STATUS}" != "failure" ];then
  exit 0
fi

# Set the correct message
if [ "${STATUS}" = "success" ]; then
  MESSAGE="✔️  Pipeline for ${CI_COMMIT_SHA:0:8} on ${CI_REPO} succeeded."
else
  MESSAGE="❌ Pipeline for \"${CI_COMMIT_MESSAGE}\" ${CI_COMMIT_SHA:0:8} on ${CI_REPO} failed.\nSee ${CI_PIPELINE_URL}"
fi

#slixsend -j anon.azylum.org -p foo -m -t kaliko@conf.azylum.org "${MESSAGE}"
printf "%s" "${MESSAGE}" | go-sendxmpp --anonymous -u "anon.azylum.org" -a woodpecker -c kaliko@conf.azylum.org || echo "❌ Failed to send notification!"
