import json
from decimal import Decimal

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rest_framework import serializers

from apps.ass_api.client import ASSAPIClient
from apps.ass_api.models import ASSAPICallLog
from apps.ass_api.sanitizers import sanitize_error_message, sanitize_value
from apps.reference_data.services import quote_product_code

from ...models import Quote
from ...services import (
    ASS_RC_ENDPOINT_BY_PRODUCT_TYPE,
    ASS_RC_METHOD_BY_PRODUCT_TYPE,
    build_quote_ass_payload_preview,
)


class Command(BaseCommand):
    help = (
        "Previsualise le payload de calcul RC ASS d'un devis et, avec "
        "confirmation explicite, appelle l'API ASS sandbox sans persister "
        "les montants calcules sur le devis."
    )

    def add_arguments(self, parser):
        parser.add_argument("quote_id", type=int)
        parser.add_argument(
            "--rc-discount-amount",
            default=Decimal("0.00"),
            type=Decimal,
            help="Montant de remise RC a inclure dans le payload de validation.",
        )
        parser.add_argument(
            "--confirm-external-ass-call",
            action="store_true",
            help="Autorise l'appel externe ASS apres verification du payload.",
        )
        parser.add_argument(
            "--allow-non-sandbox-base-url",
            action="store_true",
            help=(
                "Autorise un ASS_BASE_URL qui ne contient ni 'test' ni 'sandbox'. "
                "A utiliser seulement si l'URL fournie par ASS est bien une sandbox."
            ),
        )

    def handle(self, *args, **options):
        quote = self._get_quote(options["quote_id"])
        preview = self._build_preview(
            quote,
            rc_discount_amount=options["rc_discount_amount"],
        )

        self.stdout.write(self._json({"ass_payload_preview": sanitize_value(preview)}))

        if not options["confirm_external_ass_call"]:
            self.stdout.write(
                self.style.WARNING(
                    "Aucun appel externe ASS effectue. Relancer avec "
                    "--confirm-external-ass-call apres verification du payload."
                )
            )
            return

        self._validate_before_external_call(
            allow_non_sandbox_base_url=options["allow_non_sandbox_base_url"],
        )

        product_code = quote_product_code(quote)
        method_name = ASS_RC_METHOD_BY_PRODUCT_TYPE.get(product_code, "calculate_rc")
        try:
            response_payload = getattr(ASSAPIClient(), method_name)(
                preview["payload"],
                partner_group=quote.partner_group,
            )
        except (httpx.HTTPError, serializers.ValidationError) as exc:
            self._write_last_ass_error(quote)
            raise CommandError(
                f"Appel ASS echoue: {sanitize_error_message(str(exc))}"
            ) from exc

        self.stdout.write(
            self._json(
                {
                    "ass_response": sanitize_value(response_payload),
                    "persisted_quote_calculation": False,
                }
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Appel ASS termine. La reponse est journalisee et le devis "
                "n'a pas ete mis a jour."
            )
        )

    def _get_quote(self, quote_id):
        try:
            return Quote.objects.select_related(
                "partner_group",
                "client",
                "vehicle",
                "contributor",
                "product_reference",
                "duration_option",
                "vehicle__brand_reference",
                "vehicle__genre_reference",
                "vehicle__energy_reference",
            ).get(pk=quote_id)
        except Quote.DoesNotExist as exc:
            raise CommandError(f"Devis introuvable: {quote_id}") from exc

    def _build_preview(self, quote, *, rc_discount_amount):
        try:
            return build_quote_ass_payload_preview(
                quote=quote,
                rc_discount_amount=rc_discount_amount,
            )
        except serializers.ValidationError as exc:
            raise CommandError(
                f"Payload ASS invalide: {sanitize_error_message(str(exc.detail))}"
            ) from exc

    def _validate_before_external_call(self, *, allow_non_sandbox_base_url):
        base_url = (settings.ASS_BASE_URL or "").lower()
        if not base_url:
            raise CommandError("ASS_BASE_URL est obligatoire pour appeler ASS.")
        if not allow_non_sandbox_base_url and not any(
            marker in base_url for marker in ("test", "sandbox")
        ):
            raise CommandError(
                "ASS_BASE_URL ne ressemble pas a une sandbox. Relancer avec "
                "--allow-non-sandbox-base-url uniquement apres confirmation ASS."
            )

    def _write_last_ass_error(self, quote):
        product_code = quote_product_code(quote)
        endpoint = ASS_RC_ENDPOINT_BY_PRODUCT_TYPE.get(
            product_code, "/api/v1/partner/rc.request"
        )
        log = (
            ASSAPICallLog.objects.filter(
                partner_group=quote.partner_group,
                endpoint=endpoint,
            )
            .order_by("-created_at", "-id")
            .first()
        )
        if not log:
            return

        self.stdout.write(
            self._json(
                {
                    "ass_error": {
                        "endpoint": log.endpoint,
                        "http_status_code": log.http_status_code,
                        "status": log.status,
                        "response_payload": sanitize_value(log.response_payload),
                        "error_message": sanitize_error_message(log.error_message),
                    }
                }
            )
        )

    @staticmethod
    def _json(payload):
        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
