# Deploy tracking with CloudTrail

Track CloudFormation API calls with CloudTrail.

This repo deploys a custom role that is used to track CloudTrail events, so that the events can be linked.

## Steps

1. Deploy the custom role: `make deploy-role STACK_PREFIX=<your stack prefix>`
2. Deploy the example template: `make deploy-stack STACK_PREFIX=<your stack prefix> TEMPLATE=<template name>`
3. Run `fetch_events_for_role.py` with the created role and time range to see your api calls.

> You can get the role arn by running:
> 
> `aws cloudformation describe-stacks --stack-name <your stack prefix>-role --query 'Stacks[0].Outputs[0].OutputValue' --output text`