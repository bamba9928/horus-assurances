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

Le depot contient le backend Django et un frontend web Next.js MVP. Le client
mobile reste a creer.

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
- `/api/client-space/me/`
- `/api/client-space/contracts/`
- `/api/client-space/notifications/`
- `/api/vehicles/`
- `/api/quotes/`
- `/api/contracts/`
- `/api/payments/`
- `/api/webhooks/wave/`
- `/api/webhooks/orange-money/`
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
- `WAVE_WEBHOOK_SECRET`
- `ORANGE_MONEY_WEBHOOK_SECRET`
- `PAYMENT_WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS`
- `CLIENT_ACCESS_TOKEN_TTL_DAYS`
- `CLIENT_ACCESS_MESSAGE_PROVIDER`
- `CLIENT_ACCESS_RETURN_SECRETS_IN_RESPONSE`
- `CLIENT_ACCESS_OTP_TTL_MINUTES`
- `CLIENT_ACCESS_OTP_LENGTH`
- `CLIENT_ACCESS_OTP_MAX_ATTEMPTS`
- `CLIENT_PORTAL_BASE_URL`

## Tests

Depuis `backend/` :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Les tests couvrent surtout l'isolation multi-groupe, les permissions par role,
les wallets, les paiements, les contrats, l'integration ASS preparee, les
commissions, l'audit, les notifications et le durcissement API.

Depuis `frontend/` :

```powershell
npm install
npm run test
npm run typecheck
npm run build
```

Le frontend utilise `BACKEND_API_BASE_URL`, par defaut
`http://127.0.0.1:8000/api/v1`. Les JWT backend sont conserves cote Next.js en
cookies HttpOnly via proxy interne ; ils ne sont pas stockes en `localStorage`.

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

## Webhooks paiements

Deux endpoints publics recoivent les confirmations externes :

- `/api/v1/webhooks/wave/`
- `/api/v1/webhooks/orange-money/`

Ils ne demandent pas de JWT, mais refusent les requetes sans signature valide.
Wave utilise `Wave-Signature` avec HMAC-SHA256 et timestamp. Orange Money
utilise le header `digest` HMAC-SHA256 avec `x-correlation-id` et
`x-request-date`. Les evenements sont journalises, deduplices par provider et
event id, puis appliquent automatiquement les statuts des paiements.

## Espace client

Le client final reste une entite metier `Client`, distincte des utilisateurs
internes. Un utilisateur interne autorise peut creer un lien court signe, lie a
un contrat, via :

```powershell
POST /api/v1/client-access-tokens/
```

Le jeton est stocke uniquement sous forme hashee. Le lien et le jeton brut sont
retournes une seule fois, pour envoi SMS/email futur ou remise manuelle dans le
MVP. Le jeton doit ensuite etre transmis avec :

```http
Authorization: Client-Token <token>
```

Endpoints disponibles :

- `GET /api/v1/client-access-tokens/`
- `POST /api/v1/client-access-tokens/`
- `POST /api/v1/client-access-tokens/{id}/revoke/`
- `POST /api/v1/client-access-tokens/{id}/renew/`
- `POST /api/v1/client-access-tokens/{id}/resend-link/`
- `GET /api/v1/client-space/me/`
- `GET /api/v1/client-space/contracts/`
- `GET /api/v1/client-space/contracts/{id}/documents/`
- `POST /api/v1/client-space/contracts/{id}/documents/otp/`
- `GET /api/v1/client-space/contracts/{id}/documents/attestation/`
- `GET /api/v1/client-space/contracts/{id}/documents/carte-brune/`
- `GET /api/v1/client-space/notifications/`
- `POST /api/v1/client-space/notifications/{id}/mark-read/`
- `POST /api/v1/client-space/notifications/mark-all-read/`

Le renvoi de lien passe par une abstraction de remise client. En dev/test, le
provider configure est mocke et ne contacte aucun vrai service SMS/email. Par
securite, il genere un nouveau jeton et revoque l'ancien, car le jeton clair
n'est jamais stocke.

Les URLs documentaires externes ne sont pas exposees directement dans l'espace
client. Le backend expose seulement la disponibilite des documents. Pour
telecharger une attestation ou une carte brune, le client doit demander un OTP
mocke via `/documents/otp/`, puis appeler la route de telechargement avec le
header `X-Client-OTP`. L'OTP est stocke uniquement sous forme hashee, expire
rapidement, est a usage unique et se verrouille apres trop d'essais invalides.

En local/test, `CLIENT_ACCESS_RETURN_SECRETS_IN_RESPONSE=True` permet de
recuperer le token ou l'OTP brut pour developper sans provider externe. En
production, le setting production le desactive par defaut afin que les secrets
soient remis uniquement par le provider configure.

## Etat de phase

Le depot est aligne sur une phase 16 backend MVP. Le backend expose les
endpoints attendus par le prompt initial, conserve les routes versionnees deja
utilisees par les tests et dispose d'un calcul RC ASS optionnel pour les devis
avec routage produit, incluant auto, moto, flotte, remorque, bus ecole et garage.

La phase 17 est terminee pour le MVP web interne faisable en dev : auth JWT via
cookies HttpOnly, dashboard, formulaires metier, selects relationnels, vues
detail et tests frontend. Les prochaines validations portent sur `SCHOOL_BUS`
QR, `GARAGE` RC/QR, `FLEET` RC, les callbacks sandbox Wave et Orange Money, puis
la livraison reelle SMS/email des liens et OTP client.
