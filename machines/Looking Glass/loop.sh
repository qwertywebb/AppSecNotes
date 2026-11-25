#!/bin/bash

send() {
  local currentPort="$1"
  output=$(ssh -oHostKeyAlgorithms=+ssh-rsa -oPubkeyAcceptedAlgorithms=+ssh-rsa \
           -oStrictHostKeyChecking=no -oConnectTimeout=3 \
           alice@10.49.163.111 -p "$currentPort" 2>&1)

  if echo "$output" | grep -qi "higher"; then
         echo "$currentPort""higher"
         send "$((currentPort - 1))"
  elif echo "$output" | grep -qi "lower"; then
        echo "$currentPort""lower"
        send "$((currentPort + 1))"
  else
        echo "FOUND PORT $currentPort !!!"
        echo "$output"
  fi
}

read -r -p "Порт:" port
send "$port"
