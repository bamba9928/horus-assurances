import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rest_framework import serializers

from apps.ass_api.sanitizers import sanitize_error_message, sanitize_value
from apps.payments.models import Payment

from ...models import Contract
from ...services import ASSContractIssuer, build_contract_ass_payload_preview


class Command(BaseCommand):
    help = (
        "Previsualise le payload d'emission ASS/Diotali d'un contrat et, "
        "avec confirmation explicite, appelle l'API ASS sandbox sans persister "
        "le contrat comme emis."
    )

    def add_arguments(self, parser):
        parser.add_argument("contract_id", type=int)
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
        contract = self._get_contract(options["contract_id"])
        preview = self._build_preview(contract)

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
            contract,
            allow_non_sandbox_base_url=options["allow_non_sandbox_base_url"],
        )

        response_payload = ASSContractIssuer().issue(contract)
        self.stdout.write(
            self._json(
                {
                    "ass_response": sanitize_value(response_payload),
                    "persisted_contract_issue": False,
                }
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Appel ASS termine. La reponse est journalisee et le contrat "
                "n'a pas ete marque comme emis."
            )
        )

    def _get_contract(self, contract_id):
        try:
            return Contract.objects.select_related(
                "partner_group",
                "quote",
                "payment",
                "client",
                "vehicle",
                "contributor",
            ).get(pk=contract_id)
        except Contract.DoesNotExist as exc:
            raise CommandError(f"Contrat introuvable: {contract_id}") from exc

    def _build_preview(self, contract):
        try:
            return build_contract_ass_payload_preview(contract=contract)
        except serializers.ValidationError as exc:
            raise CommandError(
                f"Payload ASS invalide: {sanitize_error_message(str(exc.detail))}"
            ) from exc

    def _validate_before_external_call(self, contract, *, allow_non_sandbox_base_url):
        if contract.status == Contract.Status.ISSUED:
            raise CommandError("Le contrat est deja emis; appel sandbox refuse.")
        if contract.status == Contract.Status.CANCELLED:
            raise CommandError("Le contrat est annule; appel sandbox refuse.")
        if contract.payment.status != Payment.Status.CONFIRMED:
            raise CommandError("Le paiement doit etre confirme avant l'appel ASS.")

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

    @staticmethod
    def _json(payload):
        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=str,
        )
