#!/usr/bin/env bash

env

if [ "${CI_PREV_PIPELINE_STATUS}" != "failure" ] && [ "${CI_PIPELINE_STATUS}" != "failure" ];then
  exit 0
fi

# Set the correct message
if [ "${CI_PIPELINE_STATUS}" = "success" ]; then
  MESSAGE="✔️  Pipeline for ${CI_COMMIT_SHA:0:8} on ${CI_REPO} succeeded."
else
  MESSAGE="❌ Pipeline for \"${CI_COMMIT_MESSAGE}\" ${CI_COMMIT_SHA:0:8} on ${CI_REPO} failed.\nSee ${CI_PIPELINE_URL}"
fi

printf "%s" "${MESSAGE}" | go-sendxmpp --anonymous -u "anon.azylum.org" -a woodpecker -c kaliko@conf.azylum.org || echo "❌ Failed to send notification!"
