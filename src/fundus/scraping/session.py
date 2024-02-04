from typing import Optional

import requests

from fundus.logging import basic_logger

_default_header = {"user-agent": "Fundus"}


class SessionHandler:
    """Object for handling  project global aiohttp.ClientSessions

    The session life cycle consists of three steps which can be repeated indefinitely:
    Build, Supply, Teardown.
    Initially there is no session build within the session handler. When a session is requested
    with get_session() either a new one is created with _session_factory() or the session handler's
    existing one returned. Every subsequent call to get_session() will return the same
    aiohttp.ClientSession object. If close_current_session() is called, the current session will be
    tear-downed and the next call to get_session() will build a new session.
    """

    def __init__(self):
        self._session: Optional[requests.Session] = None

    @staticmethod
    def _session_factory() -> requests.Session:
        """Builds a new Session

        This returns a new client session build from pre-defined configurations:
        - pool_connections: 50
        - pool_maxsize: 50
        - hooks = {'request': lambda request:}

        Returns:
            An new ClientSession
        """

        # timings: Dict[Optional[str], float] = dict()
        #
        # async def on_request_start(
        #     session: aiohttp.ClientSession, context: types.SimpleNamespace, params: aiohttp.TraceRequestStartParams
        # ):
        #     timings[params.url.host] = time.time()
        #
        # async def on_request_end(
        #     session: aiohttp.ClientSession, context: types.SimpleNamespace, params: aiohttp.TraceRequestEndParams
        # ):
        #     assert params.url.host
        #     history = params.response.history
        #     previous_status_codes = [f"({response.status})" for response in history] if history else []
        #     status_code_chain = " -> ".join(previous_status_codes + [f"({params.response.status})"])
        #     basic_logger.debug(
        #         f"{status_code_chain} <{params.method} {params.url!r}> "
        #         f"took {time.time() - timings[params.url.host if not history else history[0].url.host]} second(s)"
        #     )
        #
        # async def on_request_exception(
        #     session: aiohttp.ClientSession, context: types.SimpleNamespace, params: aiohttp.TraceRequestExceptionParams
        # ):
        #     basic_logger.debug(
        #         f"FAILED: <{params.method} {params.url}> with {str(params.exception) or type(params.exception)}"
        #     )
        #
        # trace_config = aiohttp.TraceConfig()
        # trace_config.on_request_start.append(on_request_start)
        # trace_config.on_request_end.append(on_request_end)
        # trace_config.on_request_exception.append(on_request_exception)

        session = requests.Session()

        # hooks
        hooks = {"response": lambda response, *args, **kwargs: response.raise_for_status()}
        session.hooks = hooks

        # adapters
        adapter_kwargs = {"pool_connections": 50, "pool_maxsize": 50}
        session.mount("http://", requests.adapters.HTTPAdapter(**adapter_kwargs))
        session.mount("https://", requests.adapters.HTTPAdapter(**adapter_kwargs))

        return session

    def get_session(self) -> requests.Session:
        """Requests the current build session

        If called for the first time or after close_current_session was called,
        this function will build a new session. Every subsequent call will return
        the same session object until the session is closed with close_current_session().

        Returns:
            requests.Session: The current build session
        """
        if not self._session:
            self._session = self._session_factory()
        return self._session

    def close_current_session(self) -> None:
        """Tears down the current build session

        Returns:
            None
        """
        session = self.get_session()
        basic_logger.debug(f"Close session {session}")
        session.close()
        self._session = None


session_handler = SessionHandler()