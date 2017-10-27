#!/bin/bash
if [ -n "$EMAIL" ] && [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    send_email "Rip was successful" "This is an email notification reminding you that your Rip has finished successfully. Enjoy!" &
fi
