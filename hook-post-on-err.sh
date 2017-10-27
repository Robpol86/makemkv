#!/bin/bash
if [ -n "$EMAIL" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    send_email "Rip was unsuccessful" "This is an email notification let you know that your Rip was unsuccessful." &
fi
