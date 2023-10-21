#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

import abc
import time
from datetime import timedelta
from typing import Any, Mapping, Optional, Union
from urllib import parse

import requests
from pyrate_limiter import Duration as OrgDuration
from pyrate_limiter import InMemoryBucket, Limiter
from pyrate_limiter import Rate as OrgRate
from pyrate_limiter.exceptions import BucketFullException
from requests_cache import CachedSession

Duration = OrgDuration
Rate = OrgRate


class CallRateLimitHit(Exception):
    def __init__(self, error: str, item: Any, weight: int, rate: str, time_to_wait: timedelta):
        """Constructor

        :param error: error message
        :param item: object passed into acquire_call
        :param weight: how many credits were requested
        :param rate: string representation of the rate violated
        :param time_to_wait: how long should wait util more call will be available
        """
        self.item = item
        self.weight = weight
        self.rate = rate
        self.time_to_wait = time_to_wait
        super().__init__(error)


class AbstractCallRatePolicy(abc.ABC):
    """Call rate policy interface.
    Should be configurable with different rules, like N per M for endpoint X
    """

    @abc.abstractmethod
    def try_acquire(self, request: Any, weight: int) -> None:
        """Try to acquire request

        :param request: request object representing single call to API
        :param weight: number of requests to deduct from credit
        :return:
        """


class CallRatePolicy(AbstractCallRatePolicy):
    """
    Policy to control requests rate implemented on top of PyRateLimiter lib.

    TODO: periodical clean up of the bucket
    TODO: support static window strategy, not only moving window
    TODO: support policy without limitations
    """

    def __init__(self, rates: list[Rate]):
        """Constructor

        :param rates: list of rates, the order is important and must be ascending
        """
        self._bucket = InMemoryBucket(rates)
        # Limiter will create background task that clears old requests in the bucket
        self._limiter = Limiter(self._bucket)

    def try_acquire(self, request: Any, weight: int = 1) -> None:
        while True:
            try:
                #self._limiter.try_acquire(request, weight=weight)
                return
            except BucketFullException as exc:
                item = self._limiter.bucket_factory.wrap_item(request, weight)
                # Argument 1 to "waiting" of "AbstractBucket" has incompatible type "Union[RateItem, Awaitable[RateItem]]"; expected "RateItem"
                # Incompatible types in assignment (expression has type "Union[int, Awaitable[int]]", variable has type "int")
                time_to_wait: int = self._bucket.waiting(item)  # type: ignore[assignment,arg-type]
                print(f"Rate limit hit. Waiting {time_to_wait}ms")
                time.sleep(time_to_wait / 1000)
                # raise CallRateLimitHit(
                #     error=str(exc.meta_info["error"]),
                #     item=request,
                #     weight=int(exc.meta_info["weight"]),
                #     rate=str(exc.meta_info["rate"]),
                #     time_to_wait=timedelta(milliseconds=time_to_wait),
                # )


class RequestMatcher(abc.ABC):
    """Callable that help to match request object with call rate policies."""

    @abc.abstractmethod
    def __call__(self, request: Any) -> bool:
        """

        :param request:
        :return: True if pattern matches the provided request object, False - otherwise
        """


class HttpRequestMatcher(RequestMatcher):
    """Simple implementation of RequestMatcher for http requests case"""

    def __init__(
        self,
        method: Optional[str] = None,
        url: Optional[str] = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, Any]] = None,
    ):
        """Constructor

        :param method:
        :param url:
        :param params:
        :param headers:
        """
        self._method = method
        self._url = url
        self._params = {str(k): str(v) for k, v in (params or {}).items()}
        self._headers = {str(k): str(v) for k, v in (headers or {}).items()}

    @staticmethod
    def _match_dict(obj: Mapping[str, Any], pattern: Mapping[str, Any]) -> bool:
        """Check that all elements from pattern dict present and have the same values in obj dict

        :param obj:
        :param pattern:
        :return:
        """
        return pattern.items() <= obj.items()

    def __call__(self, request: Any) -> bool:
        """

        :param request:
        :return: True if pattern matches the provided request object, False - otherwise
        """
        if isinstance(request, requests.Request):
            prepared_request = request.prepare()
        elif isinstance(request, requests.PreparedRequest):
            prepared_request = request
        else:
            return False

        if self._method is not None:
            if prepared_request.method != self._method:
                return False
        if self._url is not None and prepared_request.url is not None:
            url_without_params = prepared_request.url.split("?")[0]
            if url_without_params != self._url:
                return False
        if self._params is not None:
            parsed_url = parse.urlsplit(prepared_request.url)
            params = dict(parse.parse_qsl(str(parsed_url.query)))
            if not self._match_dict(params, self._params):
                return False
        if self._headers is not None:
            if not self._match_dict(prepared_request.headers, self._headers):
                return False
        return True


class AbstractAPIBudget(abc.ABC):
    """Interface to some API where client allowed to have N calls per T interval.

    Important: APIBudget is not doing any API calls, the end user code is responsible to call this interface
        to respect call rate limitation of the API.

    It supports multiple policies applied to different group of requests. To distinct these groups we use RequestMatchers.
    Individual policy represented by CallRatePolicy and currently supports only moving window strategy.
    """

    @abc.abstractmethod
    def add_policy(self, request_matcher: RequestMatcher, policy: CallRatePolicy) -> None:
        """Add policy for calls

        :param request_matcher: callable to match request object with corresponding policy
        :param policy: to acquire calls
        :return:
        """

    @abc.abstractmethod
    def acquire_call(self, request: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """Try to get a call from budget, will block by default

        :param request:
        :param block: when true (default) will block the current thread until call credit is available
        :param timeout: if set will limit maximum time in block, otherwise will wait until credit is available
        :raises: CallRateLimitHit - when no credits left and if timeout was set the waiting time exceed the timeout
        """


class APIBudget(AbstractAPIBudget):
    """Default APIBudget implementation"""

    def __init__(self) -> None:
        """Constructor"""
        self._policies: list[tuple[RequestMatcher, CallRatePolicy]] = []

    def add_policy(self, request_matcher: RequestMatcher, policy: CallRatePolicy) -> None:
        """Add policy for calls

        :param request_matcher: callable to match request object with corresponding policy
        :param policy: to acquire calls
        :return:
        """

        self._policies.append((request_matcher, policy))

    def acquire_call(self, request: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """Try to get a call from budget, will block by default

        :param request:
        :param block: when true (default) will block the current thread until call credit is available
        :param timeout: if set will limit maximum time in block, otherwise will wait until credit is available
        :raises: CallRateLimitHit - when no credits left and if timeout was set the waiting time exceed the timeout
        """

        for matcher, policy in self._policies:
            if matcher(request):
                self._do_acquire(request, policy, block, timeout)
                break

    def _do_acquire(self, request: Any, policy: CallRatePolicy, block: bool, timeout: Optional[float]) -> None:
        """Internal method to try to acquire a call credit

        :param request:
        :param policy:
        :param block:
        :param timeout:
        """
        try:
            policy.try_acquire(request)
        except CallRateLimitHit as exc:
            if block:
                if timeout is not None:
                    time_to_wait = min(timedelta(seconds=timeout), exc.time_to_wait)
                else:
                    time_to_wait = exc.time_to_wait

                time.sleep(time_to_wait.total_seconds())
                policy.try_acquire(request)
            else:
                raise


class SessionProxyWithCallRate:
    def __init__(self, session: Union[requests.Session, CachedSession], api_budget: APIBudget):
        """Wraps Session to take into account API call rate limits

        :param session:
        :param api_budget:
        """
        self._session = session
        self._api_budget = api_budget

    def __getattr__(self, item: str) -> Any:
        """Forward everything to original Session class

        :param item: attribute name
        :return:
        """
        return object.__getattribute__(self._session, item)

    def __setattr__(self, key: str, value: Any) -> None:
        """Forward everything to original Session class"""
        if key.startswith("_"):
            object.__setattr__(self, key, value)  # Call original __setattr__
        return object.__setattr__(self._session, key, value)

    def send(self, request: requests.PreparedRequest, **kwargs: Any) -> requests.Response:
        """Override method to respect API call rate limits

        :param request:
        :param kwargs:
        :return:
        """
        if isinstance(self._session, CachedSession):
            if not self.cache.contains(request=request):
                self._api_budget.acquire_call(request)
        else:
            self._api_budget.acquire_call(request)

        return self._session.send(request, **kwargs)