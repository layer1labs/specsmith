#!/usr/bin/env bash
# Deliberate defect: user input passed directly to eval (injection risk).

user_expression="${1:-echo missing-input}"
eval "$user_expression"
