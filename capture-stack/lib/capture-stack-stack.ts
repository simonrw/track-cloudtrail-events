import * as cdk from 'aws-cdk-lib';
import * as path from 'path';
import { Construct } from 'constructs';
import * as ssm from 'aws-cdk-lib/aws-ssm';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import * as tasks from 'aws-cdk-lib/aws-stepfunctions-tasks';
import * as lam from 'aws-cdk-lib/aws-lambda';
import * as iam from 'aws-cdk-lib/aws-iam';
import { Duration } from 'aws-cdk-lib';

export class CaptureStackStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // bucket to store cloudtrail logs
    const bucket = new s3.Bucket(this, "Bucket", {});

    // parameter to reference bucket name
    new ssm.StringParameter(this, "bucketName", {
      parameterName: 'cloudtrail-bucket-name',
      stringValue: bucket.bucketName,
    });

    // lambda function for stepfunction
    const handler = new lam.Function(this, "handler", {
      runtime: lam.Runtime.PYTHON_3_9,
      handler: "index.handler",
      code: lam.Code.fromAsset(path.join(__dirname, "handler")),
      environment: {
        BUCKET: bucket.bucketName,
      },
      timeout: Duration.seconds(60),
    });

    handler.addToRolePolicy(new iam.PolicyStatement({
      actions: ["cloudtrail:*"],
      resources: ["*"],
    }));

    // allow bucket to upload
    bucket.grantPut(handler);

    // step function states
    const waitStep = new sfn.Wait(this, "WaitStep", {
      time: sfn.WaitTime.duration(Duration.seconds(1200)),
    });
    const lambdaStep = new tasks.LambdaInvoke(this, "LambdaStep", {
      lambdaFunction: handler,
    });

    const stepFunction = new sfn.StateMachine(this, 'StepFunction', {
      definition: waitStep.next(lambdaStep),
    });

    new ssm.StringParameter(this, "stepFunctionArn", {
      parameterName: "cloudtrail-stepfunction-arn",
      stringValue: stepFunction.stateMachineArn,
    });

    new cdk.CfnOutput(this, "stepFunctionArnOutput", {
      value: stepFunction.stateMachineArn,
    });
    new cdk.CfnOutput(this, "bucketNameOutput", {
      value: bucket.bucketName,
    });
  }
}
