from dataclasses import asdict, dataclass

from django.conf import settings
from django.utils.module_loading import import_string

from .models import ClientAccessToken


@dataclass(frozen=True)
class ClientMessageDelivery:
    mock_delivery: bool
    provider: str
    delivery_channel: str
    destination: str
    message_type: str
    access_url: str = ""

    def as_payload(self):
        return asdict(self)


class MockClientMessageProvider:
    provider_name = "mock"

    def send_access_link(self, *, access_token, access_url):
        return ClientMessageDelivery(
            mock_delivery=True,
            provider=self.provider_name,
            delivery_channel=access_token.delivery_channel,
            destination=_delivery_destination(access_token),
            message_type="client_access_link",
            access_url=access_url,
        )

    def send_document_otp(self, *, otp):
        return ClientMessageDelivery(
            mock_delivery=True,
            provider=self.provider_name,
            delivery_channel=otp.delivery_channel,
            destination=_delivery_destination(otp),
            message_type="client_document_otp",
        )


def get_client_message_provider():
    provider_class = import_string(settings.CLIENT_ACCESS_MESSAGE_PROVIDER)
    return provider_class()


def _delivery_destination(access):
    if access.delivery_channel == ClientAccessToken.DeliveryChannel.EMAIL:
        return access.client.email
    if access.delivery_channel == ClientAccessToken.DeliveryChannel.SMS:
        return access.client.phone
    return ""
