#!/usr/bin/env python

"""
Fetch all events from cloudtrail matching a specific role arn between two time ranges.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
from typing import TYPE_CHECKING, Any

import boto3
import dateutil.parser

if TYPE_CHECKING:
    from mypy_boto3_cloudtrail import LookupEventsPaginator


class PrintEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        elif isinstance(o, Event):
            return dataclasses.asdict(o)
        return super().default(o)


@dataclasses.dataclass
class Event:
    event_name: str
    request_parameters: dict
    event_time: datetime

    @classmethod
    def from_raw(cls, raw_event: dict) -> Event:
        return Event(
            event_name=raw_event["eventName"],
            request_parameters=raw_event["requestParameters"],
            event_time=dateutil.parser.parse(raw_event["eventTime"]),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("role_arn")
    parser.add_argument("-s", "--start-time", required=True, type=dateutil.parser.parse)
    parser.add_argument("-e", "--end-time", required=False, type=dateutil.parser.parse)
    args = parser.parse_args()

    paginator: "LookupEventsPaginator" = boto3.client("cloudtrail").get_paginator("lookup_events")

    end_time = args.end_time or datetime.datetime.now(tz=datetime.timezone.utc)

    result = []
    for page in paginator.paginate(
        StartTime=args.start_time,
        EndTime=end_time,
    ):
        for event in page["Events"]:
            cloudtrail_event = json.loads(event["CloudTrailEvent"])
            deploy_role = (
                cloudtrail_event.get("userIdentity", {})
                .get("sessionContext", {})
                .get("sessionIssuer", {})
                .get("arn")
            )
            if deploy_role == args.role_arn:
                result.append(Event.from_raw(cloudtrail_event))

    result.sort(key=lambda e: e.event_time)
    print(json.dumps(result, indent=2, cls=PrintEncoder))
