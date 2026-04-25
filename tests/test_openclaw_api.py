import httpx
import pytest
import respx

from services.openclaw_api import OpenClawService


@respx.mock
def test_openclaw_send_posts_expected_payload_and_headers(openclaw_config) -> None:
    route = respx.post("http://localhost:9999/api/message").mock(
        return_value=httpx.Response(200, json={"reply": "ok"})
    )
    service = OpenClawService(openclaw_config)

    service.send("hello")

    request = route.calls.last.request
    assert (
        request.headers["Authorization"],
        request.read().decode("utf-8"),
    ) == ("Bearer token-123", '{"session":"main","message":"hello"}')


@respx.mock
def test_openclaw_send_returns_reply(openclaw_config) -> None:
    respx.post("http://localhost:9999/api/message").mock(
        return_value=httpx.Response(200, json={"reply": "assistant reply"})
    )
    service = OpenClawService(openclaw_config)

    reply = service.send("hello")

    assert reply == "assistant reply"


@respx.mock
def test_openclaw_send_raises_on_non_2xx(openclaw_config) -> None:
    respx.post("http://localhost:9999/api/message").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    service = OpenClawService(openclaw_config)

    with pytest.raises(httpx.HTTPStatusError):
        service.send("hello")


def test_openclaw_close_closes_client(openclaw_config, mocker) -> None:
    service = OpenClawService(openclaw_config)
    close_spy = mocker.spy(service._client, "close")

    service.close()

    assert close_spy.call_count == 1
