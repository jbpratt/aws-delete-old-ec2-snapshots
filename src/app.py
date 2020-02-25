"""
Lambda for EC2 Snapshot deletion after 120 days
"""

import json
from datetime import timedelta, date
from typing import Dict
import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore


def lambda_handler(event: Dict, context: Dict) -> Dict:

    ec2_client = boto3.client("ec2")

    experation_date = date.today() - timedelta(days=120)
    filters = [{"Name": "start-time", "Values": [experation_date.isoformat()]}]

    try:
        response = ec2_client.describe_snapshots(Filters=filters)
    except ClientError as ex:
        return {"statusCode": 500, "body": repr(ex)}

    snapshots = response.get("Snapshots")
    assert snapshots, "found no snapshots"

    if response.get("NextToken"):
        try:
            response = ec2_client.describe_snapshots(
                Filters=filters, NextToken=response.get("NextToken")
            )
        except ClientError as ex:
            return {"statusCode": 500, "body": repr(ex)}

        snapshots.append(response.get("Snapshots", []))

    for snap in snapshots:
        try:
            ec2_client.delete_snapshot(SnapshotId=snap["SnapshotId"], DryRun=True)
        except ClientError as ex:
            return {"statusCode": 500, "body": repr(ex)}

    return {
        "statusCode": 200,
        "body": json.dumps(snapshots),
    }
