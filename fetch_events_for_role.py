#!/usr/bin/env python

"""
Fetch all events from cloudtrail matching a specific role arn between two time ranges.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
from typing import TYPE_CHECKING, Any, Optional

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
class Error:
    code: Optional[str]
    message: Optional[str]

@dataclasses.dataclass
class Event:
    event_name: str
    request_parameters: dict
    event_time: datetime.datetime
    source: str
    invoker: Optional[str]
    response_elements: Any
    request_id: Optional[str]
    event_id: Optional[str]
    event_type: Optional[str]
    event_category: Optional[str]
    error: Optional[Error]
    read_only: Optional[bool]

    @classmethod
    def from_raw(cls, raw_event: dict) -> Event:
        error = None
        if raw_event.get("errorCode"):
            error = Error(code=raw_event.get("errorCode"), message=raw_event.get("errorMessage"))

        return Event(
            event_name=raw_event["eventName"],
            request_parameters=raw_event["requestParameters"],
            event_time=dateutil.parser.parse(raw_event["eventTime"]),
            source=raw_event["eventSource"],
            invoker=raw_event.get("userIdentity", {}).get("invokedBy"),
            response_elements=raw_event.get("responseElements"),
            request_id=raw_event.get("requestID"),
            event_id=raw_event.get("eventID"),
            event_type=raw_event.get("eventType"),
            event_category=raw_event.get("eventCategory"),
            error=error,
            read_only=raw_event.get("readOnly"),
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
