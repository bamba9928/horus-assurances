# Project Roadmap

Ce fichier sert de fil conducteur du projet Horus Assurances. Il doit etre mis a
jour a chaque phase importante, apres les changements de code et les tests.

## Etat actuel

Backend Django REST Framework avance jusqu'a la phase 21 cote backend. Les
referentiels ASS internes sont exposes par API et `Vehicle` / `Quote` peuvent
maintenant s'y rattacher progressivement avec fallback sur les champs
historiques. Un endpoint de resume complet de proposition permet maintenant aux
frontends d'afficher une synthese avant validation sans appel externe ASS. Une
verification locale Diotali avant emission est aussi disponible et bloque
l'emission si les prerequis locaux echouent avant tout appel ASS ; les
validations externes, la vraie flotte, la production ASS-like et les interfaces
restent a finaliser.

Stack cible :

- Backend : Django + Django REST Framework
- Base locale : SQLite
- Base production : PostgreSQL
- Authentification : JWT
- Web : Next.js / React
- Mobile : Flutter

## Synthese des phases

- Phase 1 : socle projet Django/DRF termine.
- Phase 2 : authentification interne JWT et roles utilisateurs termines.
- Phase 3 : groupes partenaires et isolation multi-groupe termines.
- Phase 4 : clients et vehicules termines.
- Phase 5 : devis et calculs internes termines.
- Phase 6 : paiements, wallets et transactions termines.
- Phase 7 : contrats et emission preparee termines.
- Phase 8 : commissions terminees.
- Phase 9 : audit, notifications et dashboard termines.
- Phase 10 : client ASS, Basic Auth et journalisation termines.
- Phase 11 : calcul RC ASS mono termine et valide en sandbox.
- Phase 12 : emission QR ASS mono preparee et extraction documentaire terminee.
- Phase 13 : terminee pour la validation generique Diotali, avec emissions
  sandbox reelles `MOTO`, `AUTO` et `TRAILER`.
- Phase 14 : backend produits avances implemente localement ; validation
  sandbox reelle `SCHOOL_BUS` RC terminee, validations `SCHOOL_BUS` QR,
  `GARAGE` et `FLEET` encore a faire.
- Phase 15 : socle webhooks paiement implemente et teste localement ; callbacks
  sandbox Wave et Orange Money encore a valider avec les providers.
- Phase 16 : terminee pour le perimetre backend/dev faisable sans provider
  externe ; livraison reelle SMS/email et mobile restent hors validation locale.
- Phase 17 : terminee pour le MVP web interne faisable en dev : frontend
  Next.js, proxy JWT HttpOnly, dashboard, formulaires metier, vues detail et
  tests frontend.
- Phase 18 : referentiels ASS backend termines pour le socle initial.
- Phase 19 : branchement progressif `Vehicle` / `Quote` sur les referentiels
  backend termine.
- Phase 20 : resume complet de proposition backend termine.
- Phase 21 : verification Diotali locale et publique avant emission terminee.
- Phase 22 : remorque metier avec 4 documents backend terminee.
- Phase 23 : mobile Flutter non demarree.

## Phases 1 a 12 formalisees

Les phases 1 a 12 n'etaient pas decrites comme blocs nommes dans le roadmap
historique. Elles sont maintenant formalisees a partir des fonctionnalites
livrees et couvertes par les tests backend.

| Phase | Objectif | Etat | Elements livres |
| --- | --- | --- | --- |
| 1 | Initialiser le backend Django REST Framework | Terminee | Projet Django, apps metier, settings local/test/production |
| 2 | Mettre en place l'authentification interne | Terminee | JWT, user custom, roles `GENERAL_ADMIN`, `GROUP_ADMIN`, `CONTRIBUTOR` |
| 3 | Isoler les groupes partenaires | Terminee | `PartnerGroup`, filtrage par groupe, permissions multi-groupes |
| 4 | Gerer clients et vehicules | Terminee | CRUD clients/vehicules, rattachement groupe/apporteur |
| 5 | Gerer devis et calculs internes | Terminee | Devis, options garanties, montants, statuts |
| 6 | Gerer paiements et wallets | Terminee | Paiements, wallets groupe, transactions, confirmations |
| 7 | Gerer contrats | Terminee | Creation depuis paiement confirme, statuts, references documentaires |
| 8 | Gerer commissions | Terminee | Regles de commission, calculs, suivi paiement commission |
| 9 | Ajouter audit, notifications et dashboard | Terminee | Audit logs, notifications internes/client, dashboard API |
| 10 | Integrer le client ASS de base | Terminee | Basic Auth ASS, logs `ASSAPICallLog`, sanitization, erreurs metier |
| 11 | Activer le calcul RC ASS mono | Terminee | `rc.request`, extraction montants, fixture sandbox RC |
| 12 | Preparer l'emission QR ASS mono | Terminee | `qrcode.request`, extraction `linkAttestation`/`linkCarteBrune`, preview payload |

## Ce qui est deja fait

- Architecture backend Django/DRF.
- Utilisateur custom avec roles :
  - `GENERAL_ADMIN`
  - `GROUP_ADMIN`
  - `CONTRIBUTOR`
- Isolation des donnees par groupe et par apporteur.
- Endpoints API versionnes `/api/v1/...`.
- Aliases initiaux `/api/...`.
- Auth JWT et endpoint `/api/auth/me/`.
- Modules :
  - `accounts`
  - `groups`
  - `clients`
  - `vehicles`
  - `quotes`
  - `payments`
  - `contracts`
  - `ass_api`
  - `commissions`
  - `audit`
  - `notifications`
  - `common`
  - `reference_data`
- Clients, vehicules, devis, paiements, wallets, contrats, commissions.
- Audit logs et notifications internes.
- Dashboard API.
- OpenAPI, Swagger, ReDoc.
- Settings separes :
  - SQLite en local
  - SQLite memoire en test
  - PostgreSQL obligatoire en production
- Calcul RC ASS `rc.request` valide en sandbox.
- Fixture contractuelle du format reel de reponse RC ASS.
- Calcul ASS optionnel sur `POST /api/v1/quotes/{id}/calculate/`.
- Validation des echecs metier ASS `operationStatus` / `status` meme quand
  HTTP renvoie 200.
- Champ `ass_product_data` sur les devis pour stocker les donnees ASS
  specifiques a un produit avant modelisation metier definitive.
- Endpoint interne authentifie de previsualisation payload RC :
  - `POST /api/v1/quotes/{id}/ass-payload-preview/`
  - construit le payload ASS par produit sans appel reseau ASS
  - accepte des overrides non persistants pour tester un produit avant calcul
- Endpoint interne authentifie de resume de proposition :
  - `GET /api/v1/quotes/{id}/summary/`
  - construit une synthese frontend/mobile sans appel reseau ASS
  - ne modifie pas `coverage_options` ni les donnees du devis
  - expose client, vehicule, referentiels resolus, validite, garanties,
    montants, commissions estimees, paiement, regle remorque, documents
    attendus et possibilite d'emission
- Endpoint interne authentifie de previsualisation payload QR :
  - `POST /api/v1/contracts/{id}/ass-payload-preview/`
  - construit le payload d'emission ASS/Diotali sans appeler ASS
  - herite de l'isolation multi-groupe/apporteur du contrat
- Endpoint interne authentifie de verification Diotali avant emission :
  - `GET /api/v1/contracts/{id}/issue-readiness/`
  - construit et valide localement le payload Diotali sans appeler ASS
  - expose les controles paiement, statut, coherence metier, produit supporte,
    payload et champs attendus en reponse
  - le service `issue_contract` reutilise cette verification avant tout appel
    externe ASS
- Endpoint interne authentifie de verification publique ApplicationTiers :
  - `GET /api/v1/contracts/{id}/diotali-verification/`
  - interroge explicitement `/applicationtiers/verify/{immatriculation}`
  - normalise l'immatriculation et renvoie le resultat Diotali public
  - est aussi utilise par `issue_contract` quand
    `AAS_PUBLIC_VERIFY_BEFORE_ISSUE` est actif, pour bloquer une emission si
    Diotali trouve deja une attestation valide couvrant la date d'effet demandee
- Endpoint documentaire contrat :
  - `GET /api/v1/contracts/{id}/documents/`
  - expose `attestation_url` et `carte_brune_url` pour les frontends web/mobile
  - herite de l'isolation multi-groupe/apporteur du contrat
- Commande sandbox protegee :
  - `python manage.py validate_ass_sandbox_issue <contract_id>`
  - affiche le payload d'emission sans appel externe par defaut
  - exige `--confirm-external-ass-call` pour appeler ASS
  - refuse les URLs qui ne ressemblent pas a une sandbox sauf confirmation
    explicite `--allow-non-sandbox-base-url`
  - ne marque pas le contrat comme emis apres l'appel de validation
- Commande sandbox RC protegee :
  - `python manage.py validate_ass_sandbox_quote_calculation <quote_id>`
  - affiche le payload de calcul RC sans appel externe par defaut
  - exige `--confirm-external-ass-call` pour appeler ASS
  - refuse les URLs qui ne ressemblent pas a une sandbox sauf confirmation
    explicite `--allow-non-sandbox-base-url`
  - ne persiste pas les montants RC sur le devis apres l'appel de validation
- Routage du calcul RC ASS par type de produit :
  - `AUTO` -> `rc.request`
  - `MOTO` -> `rc.moto`
  - `FLEET` -> `rc.flotte.request`
  - `TRAILER` -> `remorque.rc.request`
  - `SCHOOL_BUS` -> `bus.ecole.rc`
  - `GARAGE` -> `rc.garage`
- Routage emission QR par type de produit :
  - `AUTO`
  - `MOTO`
  - `FLEET`
  - `TRAILER`
  - `SCHOOL_BUS`
  - `GARAGE`
- Champs documentaires Diotali :
  - `attestation_url`
  - `carte_brune_url`
- Referentiels ASS backend exposes en lecture :
  - `ProductReference`
  - `VehicleBrand`
  - `VehicleCategory`
  - `VehicleSubCategory`
  - `VehicleGenre`
  - `EnergyType`
  - `VehicleUsage`
  - `GuaranteeReference`
  - `DurationOption`
  - `FormRule`
- Endpoints internes read-only :
  - `GET /api/v1/reference-data/products/`
  - `GET /api/v1/reference-data/vehicle-brands/`
  - `GET /api/v1/reference-data/vehicle-categories/`
  - `GET /api/v1/reference-data/vehicle-subcategories/`
  - `GET /api/v1/reference-data/vehicle-genres/`
  - `GET /api/v1/reference-data/energies/`
  - `GET /api/v1/reference-data/usages/`
  - `GET /api/v1/reference-data/guarantees/`
  - `GET /api/v1/reference-data/durations/`
  - `GET /api/v1/reference-data/form-rules/`
- Seed initial des produits, marques de base, energies, categories,
  sous-categories, genres, garanties, durees, usages et regles formulaire.
- RC et CEDEAO sont referencees comme garanties obligatoires, cochees par
  defaut et en lecture seule.
- Les genres `TPC_MOINS_3T500` et `TPC_PLUS_3T500` portent
  `requires_trailer_section=True` pour guider les frontends sans hardcode.
- `Vehicle` est branche progressivement sur les referentiels :
  - `brand_reference`
  - `genre_reference`
  - `energy_reference`
  - fallback conserve sur `brand`, `genre`, `energy`
- `Quote` est branche progressivement sur les referentiels :
  - `product_reference`
  - `duration_option`
  - fallback conserve sur `product_type`, `duration`, `periodicity` et
    `ass_product_data`
- Helpers backend de resolution ASS :
  - priorite reference active -> `ass_code` -> `code` -> champ historique
  - payloads RC et QR compatibles lorsque les FK sont absentes
- Backfill prudent des FK referentielles :
  - uniquement sur correspondance exacte et unique
  - aucune valeur forcee si la correspondance est ambigue ou absente
- Stock QR ASS :
  - non expose dans Horus par choix produit
  - gere directement dans le compte ASS natif
- Extraction des cles documentaires Diotali vues dans la documentation ASS :
  - `linkAttestation`
  - `linkCarteBrune`
  - `attestationNumber`
  - variantes avec espaces autour des noms de cles
- Emissions sandbox Diotali reelles validees sur contrats `MOTO`, `AUTO` et
  `TRAILER`.
- Fixture contractuelle de reponse QR Diotali :
  - `apps/contracts/tests/fixtures/ass_moto_qrcode_success.json`
  - `apps/contracts/tests/fixtures/ass_auto_qrcode_success.json`
  - `apps/contracts/tests/fixtures/ass_trailer_qrcode_success.json`
- Payloads ASS avances couverts par tests unitaires locaux :
  - Moto : `cylindre`, `usage`, `nombrePlace`
  - Remorque : `referenceVehicule`
  - Bus ecole : champs vehicule standards, `nombrePlace`, `puissanceFiscale`
  - Garage : `nombreCarte`
  - Flotte : `referenceFlotte` et `requests`
- CI GitHub Actions pour le backend :
  - `manage.py check`
  - `makemigrations --check --dry-run`
  - `pytest`
  - `manage.py check --deploy`
- Phase 15 backend implemente :
  - endpoints publics `POST /api/v1/webhooks/wave/` et
    `POST /api/v1/webhooks/orange-money/`
  - verification HMAC-SHA256 Wave via `Wave-Signature`
  - verification HMAC-SHA256 Orange via `digest`, `x-correlation-id` et
    `x-request-date`
  - protection anti-rejeu par tolerance de timestamp configurable
  - journal `PaymentWebhookEvent`
  - idempotence par couple provider / event id
  - confirmation automatique des paiements externes
  - marquage automatique `FAILED` / `CANCELLED` selon statut provider
  - controle montant/devise avant confirmation
- Phase 16 backend implemente :
  - `Client` reste une entite metier rattachee a un groupe/apporteur, distincte
    des utilisateurs internes
  - jetons client revocables, rotatifs et hashes via `ClientAccessToken`
  - jetons lies a `Client`, `Contract`, `PartnerGroup` et utilisateur createur
  - champs `expires_at`, `revoked_at`, `used_at` et `delivery_channel`
  - generation interne de lien court signe :
    `POST /api/v1/client-access-tokens/`
  - API interne de revocation, renouvellement et renvoi de lien :
    `POST /api/v1/client-access-tokens/{id}/revoke/`
    `POST /api/v1/client-access-tokens/{id}/renew/`
    `POST /api/v1/client-access-tokens/{id}/resend-link/`
  - authentification espace client via `Authorization: Client-Token <token>`
  - endpoint profil client `GET /api/v1/client-space/me/`
  - endpoint consultation contrats client `GET /api/v1/client-space/contracts/`
  - endpoint documents contrat client
    `GET /api/v1/client-space/contracts/{id}/documents/`
  - endpoints de redirection attestation et carte brune
  - endpoint notifications client `GET /api/v1/client-space/notifications/`
  - marquage lecture unitaire et global des notifications client
  - notifications client creees lors de la confirmation paiement et de
    l'emission contrat
  - audit logs sur creation, envoi simule, utilisation, revocation et rotation
  - OTP client hashe via `ClientAccessOtp` pour telechargements sensibles
  - generation OTP mockee via
    `POST /api/v1/client-space/contracts/{id}/documents/otp/`
  - telechargements attestation/carte brune proteges par `X-Client-OTP`
  - URLs documentaires externes masquees dans l'espace client, remplacees par
    des indicateurs de disponibilite
  - OTP a expiration courte, usage unique, rotation par nouvelle demande et
    verrouillage apres trop d'essais invalides
  - abstraction `ClientMessageProvider` avec provider mock local/test
  - flag `CLIENT_ACCESS_RETURN_SECRETS_IN_RESPONSE` pour retourner les secrets
    bruts seulement en dev/test
  - setting production qui desactive par defaut le retour API des tokens/OTP
    bruts

## Dernier etat de tests connu

- Suite complete backend : `256 passed`, `22 warnings` connus
  `drf_spectacular` / Python 3.14 le 2026-05-28
- Tests cibles ASS apres ajout Bus ecole et commande RC sandbox : `44 passed`
- Tests cibles paiements phase 15 : `26 passed`
- Tests cibles espace client phase 16 : `24 passed`
- Tests cibles clients/notifications/contrats/paiements apres OTP : `106 passed`
- `manage.py check` : OK
- `makemigrations --check --dry-run` : OK
- `manage.py check --deploy` avec settings production : OK
- CI backend ajoutee dans `.github/workflows/ci.yml`
- Frontend `npm run typecheck` : OK le 2026-05-27
- Frontend `npm run test` : `5 passed`, `18 passed` le 2026-05-27
- Frontend `npm run e2e` : Playwright `3 passed` le 2026-05-27,
  avec backend mocke et Chrome systeme local
- Referentiels ASS backend le 2026-05-28 :
  - `python manage.py check` : OK
  - `python -m pytest apps/reference_data/tests/test_reference_data_api.py` :
    `12 passed`
- Branchement `Vehicle` / `Quote` sur referentiels le 2026-05-28 :
  - `python manage.py check` : OK
  - `python manage.py makemigrations --check --dry-run` : OK
  - tests cibles reference-data / payloads ASS : `66 passed`
  - `python -m pytest` : `236 passed`, `22 warnings`
- Resume complet de proposition le 2026-05-28 :
  - tests cibles `apps/quotes/tests/test_quote_summary.py` : `4 passed`
  - `python manage.py makemigrations --check --dry-run` : OK
  - `python -m pytest` : `240 passed`, `22 warnings`
- Verification Diotali locale avant emission le 2026-05-28 :
  - tests cibles contrats :
    `python -m pytest apps/contracts/tests/test_contract_security.py apps/contracts/tests/test_contract_ass_issue.py`
    : `45 passed`
  - suite complete backend a relancer apres finalisation du chantier
- Verification publique ApplicationTiers le 2026-05-28 :
  - `python manage.py check` : OK
  - `python manage.py makemigrations --check --dry-run` : OK
  - tests cibles ASS/contrats :
    `python -m pytest apps/ass_api/tests/test_ass_api_logs.py apps/contracts/tests/test_contract_security.py apps/contracts/tests/test_contract_ass_issue.py`
    : `75 passed`
  - `python -m pytest` : `252 passed`, `22 warnings`
- Remorque metier avec 4 documents le 2026-05-28 :
  - `python manage.py check` : OK
  - `python manage.py makemigrations --check --dry-run` : OK
  - tests cibles contrats/devis :
    `python -m pytest apps/contracts/tests/test_contract_ass_issue.py apps/contracts/tests/test_contract_security.py apps/quotes/tests/test_quote_ass_calculation.py apps/quotes/tests/test_quote_summary.py`
    : `75 passed`
  - `python -m pytest` : `256 passed`, `22 warnings`

## Prochaines validations externes

Ces points ne doivent pas etre marques comme termines tant qu'une sandbox reelle
ou un choix provider n'a pas confirme le comportement.

1. ASS `SCHOOL_BUS`, `GARAGE`, `FLEET`
   - `SCHOOL_BUS` RC valide en sandbox le 2026-05-25
     (`operationStatus=SUCCESS`) et fixture non sensible figee.
   - Previsualiser les payloads RC et QR avec les endpoints internes.
   - Executer `validate_ass_sandbox_quote_calculation` sur des devis locaux de
     chaque produit avec `--confirm-external-ass-call`.
   - Executer `validate_ass_sandbox_issue` uniquement sur contrats sandbox dont
     le paiement est confirme et dont l'emission externe est autorisee.
   - Figer une fixture non sensible par reponse reelle acceptee.
2. Bus ecole Postman v1.1
   - Confirmer avec ASS si les champs optionnels de la collection Postman v1.1
     sont acceptes, ignores ou rejetes lorsqu'ils sont presents.
   - Documenter la liste definitive des champs a exposer dans l'API publique.
3. Wave et Orange Money
   - Obtenir les secrets webhook sandbox et configurer les callback URLs vers un
     environnement accessible publiquement.
   - Declencher un paiement sandbox par provider et verifier signature,
     reference transactionnelle, montant, devise, idempotence et statut final.
   - Ajouter des fixtures provider si le payload reel differe du format local.
4. Espace client
   - Choisir les providers SMS/email avant integration reelle.
   - Brancher l'envoi reel des liens et OTP apres stabilisation du format de
     message client.
   - Conserver le stockage hashe pour les secrets client et OTP.

Hors perimetre Horus :

- Stock QR ASS : ne pas exposer d'API ou workflow Horus ; gestion dans le compte
  ASS natif.

## Reste a faire

### Phase 13 - Validation emission Diotali

Objectif : valider une vraie reponse d'emission QR/document Diotali sans risquer
de polluer la production.

Etat : terminee pour la validation generique Diotali, sur emissions sandbox
reelles `MOTO`, `AUTO` et `TRAILER`.

Fait :

- Base locale SQLite initialisee avec les migrations Django.
- Contrat local de test cree pour previsualisation :
  - `contract_id=1`
  - produit `MOTO`
- Previsualiser le payload via
  `POST /api/v1/contracts/{id}/ass-payload-preview/`.
- Previsualiser ou executer prudemment l'appel sandbox via
  `python manage.py validate_ass_sandbox_issue <contract_id>`.
- Appel sandbox reel effectue avec validation explicite :
  - endpoint `/api/v1/partner/moto.request`
  - `operationStatus=SUCCESS`
  - `attestationNumber=SN004FTNNGK`
  - `linkAttestation` confirme
  - `linkCarteBrune` confirme
- Appel sandbox reel `AUTO` effectue avec validation explicite :
  - endpoint `/api/v1/partner/qrcode.request`
  - `operationStatus=SUCCESS`
  - `attestationNumber=SN004Q6BMD5`
  - `linkAttestation` confirme
  - `linkCarteBrune` confirme
- Appel sandbox reel `TRAILER` effectue avec validation explicite :
  - endpoint `/api/v1/partner/remorque.qrcode.request`
  - reference du tracteur confirmee : `referenceExterne` AUTO, pas
    immatriculation ni numero d'attestation
  - `operationStatus=SUCCESS`
  - `attestationNumber=SN004NFKDEI`
  - `linkAttestation` confirme
  - `linkCarteBrune` confirme
  - premiere remorque emise avec `responsabiliteCivile=0`, conformement a la
    documentation ASS
- Fixture non sensible figee dans
  `apps/contracts/tests/fixtures/ass_moto_qrcode_success.json`.
- Fixture non sensible figee dans
  `apps/contracts/tests/fixtures/ass_auto_qrcode_success.json`.
- Fixture non sensible figee dans
  `apps/contracts/tests/fixtures/ass_trailer_qrcode_success.json`.
- Test contractuel ajoute pour verifier l'extraction depuis la fixture reelle.

Reserve :

- Cette phase valide le format Diotali et les cles documentaires sur un premier
  produit. Les emissions sandbox par produit restent a derouler dans la phase
  14.

### Phase 14 - Produits ASS avances

Objectif : completer les payloads par produit.

Etat : demarree, avec payloads locaux et routage backend couverts par tests.

Fait :

- Auto : flux `rc.request` conserve, options garanties `garantiesOptPT`,
  `garantiesOptAR`, `garantiesOptAS` ajoutees, emission sandbox validee.
- Moto : payloads RC/QR enrichis avec `cylindre`, `usage`, `nombrePlace`.
- Remorque : payload RC et payload QR exigent `referenceVehicule`; sandbox
  confirmee avec la
  `referenceExterne` du tracteur AUTO et RC a `0` pour la premiere remorque.
- Garage : payloads RC/QR gerent `nombreCarte`.
- Bus ecole : produit `SCHOOL_BUS` ajoute cote devis, avec routage RC
  `bus.ecole.rc`, routage QR `bus.ecole.request` et payloads locaux alignes sur
  la documentation ASS fournie ; appel sandbox RC reel valide le 2026-05-25
  avec `operationStatus=SUCCESS`.
- Flotte : payload RC accepte `referenceFlotte` et `requests`, avec fallback
  mono-vehicule local.
- Tests payload/routage ajoutes pour calcul RC et emission QR.
- Previsualisation RC/QR securisee ajoutee pour verifier les payloads produits
  avant appel sandbox.
- Commande locale de validation sandbox RC ajoutee pour tester les calculs ASS
  produit sans modifier les devis.

Reste a faire :

- Valider `SCHOOL_BUS` QR, `GARAGE` RC/QR et `FLEET` RC en sandbox ASS sans
  emission de production.
- Confirmer les champs exacts a exposer dans l'API publique au lieu de garder
  seulement `ass_product_data`.
- Flotte : modeliser proprement le multi-vehicules si le produit doit gerer de
  vraies flottes dans Horus.
- Garage : confirmer les genres metier attendus et la valeur par defaut de
  `nombreCarte`.
- Bus ecole : confirmer en sandbox les genres `BE-VTA` / `BE-VTCATP` et la
  tolerance ASS vis-a-vis des champs optionnels presents dans la collection
  Postman v1.1.

### Phase 15 - Paiements externes

Objectif : passer des paiements modelises aux webhooks reels.

Etat : socle backend implemente et teste localement ; validation provider
sandbox restante.

Fait :

- Wave webhook.
- Orange Money webhook.
- Verification de signature.
- Idempotence webhook.
- Protection contre rejeu.
- Mise a jour automatique des statuts.
- Tests de securite.

Reste a faire :

- Confirmer avec les contrats providers les noms exacts des champs de reference
  transactionnelle Wave et Orange Money.
- Tester un vrai callback sandbox Wave.
- Tester un vrai callback sandbox Orange Money.
- Ajouter, si necessaire, des adaptateurs de payload par pays/provider si les
  webhooks reels different du format generique documente.

### Phase 16 - Espace client

Objectif : permettre au client final de consulter ses documents.

Etat : termine pour le backend faisable en dev sans provider externe ; livraison
reelle et interfaces restantes.

Fait :

- Clarifier si `Client` devient un utilisateur connecte ou reste une entite
  rattachee a un apporteur.
- Modele `ClientAccessToken` lie au client, contrat, groupe et createur.
- Stockage uniquement du hash du jeton.
- Expiration, revocation, utilisation et canal de remise.
- Services de generation, verification, revocation, rotation et renvoi simule.
- API interne admin/apporteur pour creer, revoquer, renouveler et renvoyer un
  lien.
- Endpoint consultation contrats client.
- Telechargement attestation.
- Telechargement carte brune.
- Notifications client.
- OTP documents sensibles hashe, expire, usage unique et verrouillable.
- Provider de remise client abstrait avec implementation mock local/test.
- Retour des secrets bruts configurable et desactive par defaut en production.
- Tests de securite : expiration, revocation, autre groupe, rotation, absence de
  stockage clair, refus document sans jeton valide, OTP expire/revoque/usage
  unique/mauvais usage/verrouillage.
- Portail client web minimal ajoute en phase 17 avec session client en cookie
  HttpOnly via proxy Next.js.

Reste a faire :

- Hors dev local : choisir et brancher un vrai provider SMS/email.
- Hors dev local : valider les formats de messages client avec le provider.
- Mobile : ajouter les ecrans de consultation client.

### Phase 17 - Frontend Next.js

Objectif : dashboard web.

Contraintes design :

- Interface blanche.
- Police noire lisible.
- Icons professionnelles.
- UI sobre, dense et orientee gestion.

Etat : terminee pour le MVP web interne faisable en dev.

Fait :

- Application Next.js dans `frontend/`.
- Authentification JWT via proxy Next.js ; les tokens sont stockes en cookies
  HttpOnly et ne sont plus exposes au navigateur via `localStorage`.
- Shell applicatif protege avec navigation adaptee au role utilisateur.
- Dashboard connecte a `/api/v1/dashboard/`.
- Pages de gestion pour groupes, utilisateurs, apporteurs, clients,
  vehicules, devis, paiements, contrats, acces client, commissions, wallets,
  audit logs et notifications.
- Formulaires metier avec champs dedies, selects relationnels et conversion
  des payloads avant envoi backend.
- Formulaires metier ameliores avec sections lisibles, contraintes de saisie,
  validations frontend prudentes et editeurs guides pour les garanties et
  donnees produit ASS par produit.
- Recherche, pagination, vues detail metier, creation, modification et
  suppression quand l'endpoint backend l'autorise.
- Actions internes prudentes exposees pour paiements, notifications et jetons
  client.
- Garde-fous frontend renforces pour les actions sensibles exposees :
  confirmation par saisie explicite, raisons de desactivation par statut,
  messages metier et blocage de l'execution si la previsualisation requise
  echoue.
- Action d'emission ASS/QR exposee sur les contrats avec previsualisation
  obligatoire du payload `ass-payload-preview` avant appel `issue`.
- Portail client web minimal sur `/client` et `/client-space/access`, avec
  jeton client conserve cote Next.js en cookie HttpOnly et proxy interne
  `/api/client-space`.
- Consultation profil client, contrat lie au jeton, disponibilite documents,
  demande OTP mockee et ouverture d'attestation/carte brune apres OTP valide.
- Suite de tests frontend automatisee avec Vitest.
- Suite E2E navigateur Playwright ajoutee avec fixtures mockees stables pour
  couvrir la confirmation d'emission ASS/QR et le parcours portail client
  OTP + ouverture document.
- Override `postcss` applique pour corriger l'audit npm sans downgrade Next.js.

Taches :

- Brancher les E2E navigateur sur un vrai seed backend stable quand il sera
  disponible, en complement des fixtures mockees actuelles.
- Etendre la couverture E2E aux workflows internes de creation/modification
  metier lorsque le seed stable couvrira groupes, clients, vehicules, devis,
  paiements et contrats.

### Phase 18 - Referentiels ASS backend

Objectif : centraliser les valeurs compatibles ASS dans le backend pour eviter
les hardcodes Next.js et Flutter.

Etat : termine pour le socle initial backend.

Fait :

- App Django `reference_data`.
- Modeles :
  - `ProductReference`
  - `VehicleBrand`
  - `VehicleCategory`
  - `VehicleSubCategory`
  - `VehicleGenre`
  - `EnergyType`
  - `VehicleUsage`
  - `GuaranteeReference`
  - `DurationOption`
  - `FormRule`
- Relations categorie -> sous-categorie -> genre.
- Flag `requires_trailer_section` sur les genres vehicule.
- Garanties RC et CEDEAO obligatoires, selectionnees par defaut et readonly.
- Champs de tracabilite sur les referentiels :
  - `source`
  - `is_verified`
  - `metadata`
- Endpoints `GET /api/v1/reference-data/...` en lecture seule.
- Filtres utiles par `code`, `category_code`, `subcategory_code`,
  `product_code`, `genre_code`, `is_active`.
- Seed initial via migration.
- Admin Django pour gestion interne des valeurs.
- Tests backend cibles.

Reste a faire :

- Enrichir le seed avec les valeurs observees dans la documentation ASS, la
  collection Postman, le compte natif ASS et les validations sandbox reussies.
- Ne pas considerer les valeurs seed comme exhaustives : elles portent
  `metadata.is_exhaustive=False`.
- Passer progressivement `is_verified=True` uniquement apres validation sandbox
  reussie de la valeur concernee.
- Completer ou corriger les `ass_code` / codes externes lorsqu'une valeur est
  confirmee, sans bloquer le projet sur une liste officielle exhaustive.
- Brancher Next.js et Flutter sur ces endpoints sans recoder les valeurs en dur.
- Ajouter une validation backend des garanties obligatoires lors du prochain
  chantier `Quote`.

### Phase 19 - Branchement Vehicle / Quote sur referentiels

Objectif : permettre a Horus d'utiliser les referentiels backend dans les
vehicules et devis sans casser les anciennes donnees ni les payloads ASS.

Etat : termine pour la tranche backend progressive.

Fait :

- FK optionnelles ajoutees sur `Vehicle` :
  - `brand_reference`
  - `genre_reference`
  - `energy_reference`
- FK optionnelles ajoutees sur `Quote` :
  - `product_reference`
  - `duration_option`
- Champs historiques conserves comme fallback :
  - `Vehicle.brand`, `Vehicle.genre`, `Vehicle.energy`
  - `Quote.product_type`, `Quote.duration`, `Quote.periodicity`,
    `Quote.ass_product_data`
- Serializers `Vehicle` et `Quote` exposes avec ids, codes et labels des
  references.
- Creation API compatible FK ou texte historique.
- Payloads RC ASS et QR ASS mis a jour pour utiliser les helpers de resolution.
- Routage calcul RC et emission QR compatible `product_reference`.
- Migrations de backfill prudentes, sans matching agressif.
- Tests ajoutes pour :
  - creation `Vehicle` avec et sans FK
  - creation `Quote` avec et sans FK
  - `DurationOption`
  - payload ASS avec FK
  - payload ASS sans FK
  - garanties RC / CEDEAO obligatoires, selectionnees et readonly

Reste a faire :

- Valider cote produit si les garanties RC / CEDEAO doivent etre enforcees au
  moment de la validation finale du devis.
- Brancher les formulaires Next.js sur `/api/v1/reference-data/...`.
- Preparer Flutter sur les memes endpoints.

### Phase 20 - Resume complet de proposition

Objectif : fournir aux frontends Next.js et Flutter un resume lisible du devis
avant validation, proche du recapitulatif du compte natif ASS.

Etat : termine pour la tranche backend locale et la verification publique
ApplicationTiers avant emission.

Fait :

- Endpoint `GET /api/v1/quotes/{id}/summary/`.
- Isolation multi-groupe et apporteur heritee du `QuoteViewSet`.
- Resume sans appel externe ASS et sans mutation du devis.
- Fallbacks conserves si les FK referentielles sont absentes.
- Utilisation des FK actives quand elles existent pour marque, genre, energie,
  produit et duree.
- Validite exposee avec date d'effet, date d'expiration stockee ou calculable,
  duree et periodicite.
- Garanties RC et CEDEAO exposees comme obligatoires, selectionnees et readonly.
- Garanties optionnelles visibles avec etat de selection depuis
  `coverage_options`.
- Montants exposes : RC, prime, frais, commission apporteur estimee,
  commission groupe si applicable, net apres commission et total a verser.
- Statut du dernier paiement lie au devis.
- Regle remorque exposee depuis `FormRule` en priorite, avec fallback
  `requires_trailer_section`.
- Documents attendus apres emission : attestation et carte brune CEDEAO.
- Indicateur `can_issue` avec raisons de blocage.
- Tests backend dedies.

Reste a faire :

- Brancher Next.js sur ce resume avant validation du devis/paiement.
- Brancher Flutter sur le meme endpoint.
- Valider avec le metier si le libelle `total_to_pay` doit rester le TTC Horus
  actuel ou afficher une decomposition differente dans l'UI.

### Phase 21 - Verification Diotali avant emission

Objectif : verifier qu'un contrat est pret pour Diotali avant de declencher une
emission externe ASS, puis permettre une verification explicite de
l'immatriculation sur l'API publique ApplicationTiers.

Etat : termine pour la tranche backend locale et publique.

Fait :

- Endpoint `GET /api/v1/contracts/{id}/issue-readiness/`.
- Controle sans appel externe ASS.
- Construction locale du payload QR/Diotali par produit.
- Verification du statut contrat, paiement confirme, montant paye, coherence
  contrat/devis/paiement/client/vehicule, produit supporte et presence des
  references minimales dans le payload.
- Reutilisation du meme controle dans `issue_contract` avant instanciation du
  client ASS/Diotali.
- Blocage de l'emission avant appel externe si la verification locale echoue.
- Exposition des champs de reponse Diotali attendus pour contrat, attestation et
  carte brune.
- Client public `ApplicationTiersPublicClient`.
- Settings `AAS_PUBLIC_BASE_URL` et `AAS_PUBLIC_TIMEOUT_SECONDS`.
- Endpoint `GET /api/v1/contracts/{id}/diotali-verification/` pour declencher
  explicitement la verification publique par immatriculation.
- Normalisation locale des immatriculations avant appel
  `/applicationtiers/verify/{immatriculation}`.
- Normalisation du resultat ApplicationTiers dans un bloc `verification` :
  statut, validite, numero attestation, immatriculation, dates, marque et
  modele, tout en conservant le payload brut `result`.
- Si ApplicationTiers renvoie `SUCCESS` pour une attestation qui couvre la date
  d'effet demandee, `issue_contract` bloque l'emission avant tout appel ASS et
  renvoie l'attestation existante, l'echeance, une date d'effet conseillee et un
  message demandant a l'utilisateur de corriger la date d'effet ou d'abandonner.
- Le blocage public avant emission est configurable par
  `AAS_PUBLIC_VERIFY_BEFORE_ISSUE`.
- Tests backend pour cas pret, payload produit invalide, blocage avant appel ASS
  verification publique ApplicationTiers et permissions multi-groupe/apporteur.

Reste a faire :

- Brancher Next.js sur `issue-readiness` avant l'action `issue`.
- Brancher Next.js sur `diotali-verification` comme verification explicite
  avant emission quand le gestionnaire veut consulter ApplicationTiers.
- Confirmer si certains champs optionnels doivent devenir bloquants selon le
  produit ASS.
### Phase 22 - Remorque metier avec 4 documents

Objectif : modeliser le flux remorque sans ajouter de frontend, en s'appuyant
sur `referenceVehicule` comme reference ASS du vehicule tracteur et en exposant
les quatre documents attendus.

Etat : termine pour la tranche backend locale.

Fait :

- Helper remorque pour resoudre `referenceVehicule` depuis `ass_product_data`
  ou depuis un contrat tracteur local emis via un id de contrat.
- Payload RC remorque et payload QR remorque exigent desormais
  `referenceVehicule`; le fallback immatriculation n'est plus utilise pour
  emettre une remorque.
- `referenceExterne` renvoyee par ASS/Diotali est conservee comme
  `contract_number`, afin de pouvoir etre reutilisee comme reference du
  tracteur pour une remorque.
- `GET /api/v1/contracts/{id}/documents/` conserve les champs historiques
  `attestation_url` et `carte_brune_url`, et ajoute une liste `documents`.
- Pour une remorque liee a un contrat tracteur Horus emis pour le meme client,
  la liste `documents` expose quatre pieces :
  - attestation vehicule tracteur ;
  - carte brune CEDEAO vehicule tracteur ;
  - attestation remorque ;
  - carte brune CEDEAO remorque.
- `issue-readiness` bloque une remorque sans `referenceVehicule` avant tout
  appel ASS et expose les quatre documents attendus.
- Le resume de proposition expose les quatre documents attendus pour un devis
  remorque, avec disponibilite des documents tracteur si le contrat local est
  retrouve.
- Tests backend ajoutes pour reference remorque obligatoire, readiness,
  extraction `referenceExterne`, documents a quatre entrees et resume devis.

Reste a faire :

- Brancher Next.js sur la selection du contrat tracteur et l'affichage des
  quatre documents.
- Brancher Flutter sur le meme contrat documentaire.
- Confirmer en sandbox si ASS accepte toujours `referenceVehicule` derivee du
  `referenceExterne` stocke comme `contract_number` dans tous les cas.

### Phase 23 - Mobile Flutter

Objectif : application mobile apporteur/client.

Taches :

- Connexion JWT.
- Creation client.
- Creation vehicule.
- Devis.
- Suivi contrat.
- Suivi commission.
- Documents attestation/carte brune, avec cas remorque a quatre documents.

## Risques techniques

- Emission QR reelle ASS/Diotali peut creer une transaction externe.
- Les noms de cles Diotali doivent etre confirmes sur une reponse reelle.
- Certains produits ASS demandent encore une modelisation metier definitive ;
  `ass_product_data` est une solution transitoire controlee.
- Les nouveaux referentiels ASS exposent un seed initial non exhaustif ; les
  valeurs doivent conserver leur `source` et leur statut `is_verified` pour
  eviter de bloquer le projet sur une liste officielle qui peut ne pas exister.
- Le resume de proposition utilise les montants deja presents sur le devis ; il
  ne recalcule pas la RC ASS et ne garantit donc pas qu'un devis non calcule est
  pret pour emission.
- La commission du resume est une estimation basee sur la regle active au
  moment de la consultation ; elle peut differer si la regle change avant
  emission/generation definitive.
- Si `referenceVehicule` pointe vers un contrat tracteur externe non present
  dans Horus, l'emission remorque peut rester possible mais les deux documents
  tracteur ne seront pas disponibles localement.
- La verification Diotali avant emission reste locale : elle valide le payload
  et les prerequis Horus, mais ne garantit pas que Diotali acceptera la requete
  lors d'un appel sandbox ou production.
- Les payloads produits avances sont testes localement, mais pas encore valides
  contre une sandbox ASS reelle.
- Le stock QR ASS n'est pas un risque fonctionnel Horus : il reste gere dans le
  compte ASS natif.
- Les signatures et payloads reels Wave/Orange Money doivent encore etre
  confirmes en sandbox provider.
- Les liens et OTP client ne sont pas encore envoyes par vrai provider
  SMS/email.
- Les E2E navigateur frontend utilisent actuellement des fixtures mockees ;
  le seed backend stable reste a definir pour valider les parcours bout en bout
  contre une base reelle.
- Le frontend web Next.js MVP existe ; le mobile Flutter n'est pas encore cree.

## Regle de maintenance

Apres chaque phase ou intervention significative :

- mettre a jour ce fichier ;
- ajouter les nouvelles fonctionnalites terminees ;
- deplacer les taches terminees hors du reste a faire ;
- noter les tests executes et leur resultat ;
- noter les risques ou points bloquants restants.
