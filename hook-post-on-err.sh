#!/bin/bash
if [ -z "$EMAIL" ] && [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    send_email "Rip was unsuccessful" "This is an email notification let you know that your Rip was unsuccessful." &
fi
