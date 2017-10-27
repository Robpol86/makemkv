#!/bin/bash
if [ -z "$EMAIL" ] && [ -z "$AWS_ACCESS_KEY_ID" ] && [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    send_email "Rip was successful" "This is an email notification reminding you that your Rip has finished successfully. Enjoy!" &
fi
