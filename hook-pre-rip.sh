#!/bin/bash
send_email () {
    aws ses send-email --region us-west-2 --output json --from $EMAIL --to $EMAIL --subject "$1" --text "$2"
}
