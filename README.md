# Horus Assurances

Plateforme d'assurance multi-groupes avec backend Django REST Framework.

## Objectif

La plateforme isole les donnees par groupe partenaire. Un admin general voit toute
la plateforme, un admin de groupe voit uniquement son groupe, et un apporteur voit
ses propres donnees.

Stack cible :

- Backend : Django, Django REST Framework, JWT
- Base de donnees : PostgreSQL
- Web : Next.js / React
- Mobile : Flutter

Le depot actuel contient le backend. Les clients web et mobile restent a creer.

## Modules backend

- `accounts` : utilisateurs, roles et permissions
- `groups` : groupes partenaires independants
- `clients` : clients rattaches a un groupe
- `vehicles` : vehicules rattaches a un client et a un groupe
- `quotes` : devis
- `payments` : paiements, wallets et transactions
- `contracts` : contrats et emission d'attestations
- `ass_api` : client et logs pour l'API ASS
- `commissions` : regles et commissions des apporteurs
- `audit` : journal d'activite
- `notifications` : notifications internes
- `common` : pagination, endpoints communs et dashboard

## Roles

- `GENERAL_ADMIN` : acces global, gestion des groupes et des admins.
- `GROUP_ADMIN` : acces limite a son groupe.
- `CONTRIBUTOR` : acces limite a ses clients, vehicules, devis, contrats,
  paiements et commissions.

Chaque client, vehicule, devis, paiement, contrat et commission est rattache a un
groupe. Les viewsets filtrent les querysets selon le role connecte.

## Endpoints principaux

Les endpoints historiques versionnes restent disponibles sous `/api/v1/`.
Des aliases compatibles avec le prompt initial sont aussi exposes sous `/api/`.

- `/api/auth/login/`
- `/api/auth/me/`
- `/api/groups/`
- `/api/users/`
- `/api/contributors/`
- `/api/clients/`
- `/api/vehicles/`
- `/api/quotes/`
- `/api/contracts/`
- `/api/payments/`
- `/api/commissions/`
- `/api/dashboard/`
- `/api/schema/`
- `/api/docs/`
- `/api/redoc/`

## Configuration

Les secrets doivent rester dans les variables d'environnement. Ne pas commiter de
fichier `.env` avec des identifiants reels.

En local, `config.settings.local` utilise SQLite dans `backend/db.sqlite3`.
En production, `config.settings.production` force PostgreSQL et exige les
variables `DATABASE_NAME`, `DATABASE_USER` et `DATABASE_HOST`.

Variables importantes :

- `DJANGO_SETTINGS_MODULE` (`config.settings.local`, `config.settings.test` ou
  `config.settings.production`)
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECURE_SSL_REDIRECT`
- `DJANGO_SECURE_HSTS_SECONDS`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS`
- `DJANGO_SECURE_HSTS_PRELOAD`
- `DATABASE_ENGINE`
- `DATABASE_NAME`
- `DATABASE_USER`
- `DATABASE_PASSWORD`
- `DATABASE_HOST`
- `DATABASE_PORT`
- `ASS_BASE_URL`
- `ASS_USERNAME`
- `ASS_PASSWORD`

## Tests

Depuis `backend/` :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Les tests couvrent surtout l'isolation multi-groupe, les permissions par role,
les wallets, les paiements, les contrats, l'integration ASS preparee, les
commissions, l'audit, les notifications et le durcissement API.

## Calcul ASS des devis

L'action `POST /api/v1/quotes/{id}/calculate/` conserve le mode manuel existant.
Pour declencher un calcul RC via ASS, envoyer `use_ass: true`. Le backend construit
alors le payload `rc.request`, appelle le client ASS configure par variables
d'environnement, extrait les montants de la reponse et met le devis en statut
`CALCULATED`.

Exemple :

```json
{
  "use_ass": true,
  "coverage_options": [1, 2, 4],
  "fees_amount": "3000.00"
}
```

Le format reel valide en sandbox pour `rc.request` est fige dans les tests. ASS
renvoie notamment `PrimeRC`, `PrimeAG`, `CoutPolice`, `PrimeTotale`, `Taxe`,
`Fga`, `Cedeao`, `data`, `operationStatus` et `code`.

## Emission QR ASS

L'emission des contrats route l'appel QR selon le type de produit du devis :

- `AUTO` : `qrcode.request`
- `MOTO` : `moto.request`
- `FLEET` : `qrcode.flotte.request`
- `TRAILER` : `remorque.qrcode.request`
- `SCHOOL_BUS` : `bus.ecole.request`
- `GARAGE` : `garage.request`

Les reponses ASS/Diotali peuvent fournir deux liens documentaires : un lien
attestation et un lien carte brune. Le backend les expose dans les champs dedies
`attestation_url` et `carte_brune_url`, sans les melanger avec les references ASS.

Pour valider prudemment les payloads ASS en sandbox depuis une base locale :

```powershell
python manage.py validate_ass_sandbox_quote_calculation <quote_id>
python manage.py validate_ass_sandbox_issue <contract_id>
```

Ces commandes affichent les payloads sans appel externe par defaut. L'appel ASS
necessite `--confirm-external-ass-call` et ne persiste pas le resultat sur le
devis ou le contrat.

## Etat de phase

Le depot est aligne sur une phase 14 partielle. Le backend expose les endpoints
attendus par le prompt initial, conserve les routes versionnees deja utilisees
par les tests et dispose d'un calcul RC ASS optionnel pour les devis avec
routage produit, incluant auto, moto, flotte, remorque, bus ecole et garage.

La suite peut maintenant se concentrer sur les validations sandbox ASS restantes,
les webhooks de paiement et la preparation des clients web/mobile.
