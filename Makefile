STACK_PREFIX :=
TEMPLATE :=

deploy-role: check-stack-prefix
	aws cloudformation deploy --stack-name ${STACK_PREFIX}-role --template role.yml \
		--parameter-overrides RoleName=${STACK_PREFIX}-role \
		--capabilities CAPABILITY_NAMED_IAM

delete-role: check-stack-prefix
	aws cloudformation delete-stack --stack-name ${STACK_PREFIX}-role
	aws cloudformation wait stack-delete-complete --stack-name ${STACK_PREFIX}-role

deploy-stack: check-stack-prefix check-template
	export ROLE_ARN=$(shell aws cloudformation describe-stacks --stack-name ${STACK_PREFIX}-role --query 'Stacks[0].Outputs[0].OutputValue' --output text); \
	aws cloudformation deploy --stack-name ${STACK_PREFIX}-stack --template ${TEMPLATE} \
		--capabilities CAPABILITY_NAMED_IAM \
		--role-arn $$ROLE_ARN \
		--parameter-overrides Prefix=${STACK_PREFIX} BucketName=${STACK_PREFIX}-bucket-3e675111-4374-4b15-a631-5ad17ae8dd34


delete-stack: check-stack-prefix
	aws cloudformation delete-stack --stack-name ${STACK_PREFIX}-stack
	aws cloudformation wait stack-delete-complete --stack-name ${STACK_PREFIX}-stack

check-stack-prefix:
ifndef STACK_PREFIX
	$(error STACK_PREFIX is undefined)
endif

check-template:
ifndef TEMPLATE
	$(error TEMPLATE is undefined)
endif
