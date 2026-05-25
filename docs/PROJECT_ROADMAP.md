# Project Roadmap

Ce fichier sert de fil conducteur du projet Horus Assurances. Il doit être mis à
jour à chaque phase importante, apres les changements de code et les tests.

## État actuel

Backend Django REST Framework avance jusqu'à la phase 16 cote backend. Les
socles locaux des phases 15 et 16 sont implementes et testes ; les validations
externes et interfaces restent à finaliser.

Stack cible :

- Backend : Django + Django REST Framework
- Base locale : SQLite
- Base production : PostgreSQL
- Authentification : JWT
- Web : Next.js / React
- Mobile : Flutter

## Synthese des phases

- Phase 13 : terminée pour la validation générique Diotali, avec emissions
  sandbox réelles `MOTO`, `AUTO` et `TRAILER`.
- Phase 14 : backend produits avances implemente localement ; validations
  sandbox réelles `GARAGE`, `FLEET` et `SCHOOL_BUS` encore a faire.
- Phase 15 : socle webhooks paiement implemente et teste localement ; callbacks
  sandbox Wave et Orange Money encore a valider avec les providers.
- Phase 16 : terminée pour le périmètre backend/dev faisable sans provider
  externe ; livraison réelle SMS/email et interfaces frontend/mobile restent
  hors validation locale.
- Phase 17 : non démarrée.
- Phase 18 : non démarrée.

## Ce qui est deja fait

- Architecture backend Django/DRF.
- Utilisateur custom avec roles :
  - `GENERAL_ADMIN`
  - `GROUP_ADMIN`
  - `CONTRIBUTOR`
- Isolation des donnees par groupe et par apporteur.
- Endpoints API versionnés `/api/v1/...`.
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
- Clients, vehicules, devis, paiements, wallets, contrats, commissions.
- Audit logs et notifications internes.
- Dashboard API.
- OpenAPI, Swagger, ReDoc.
- Settings separes :
  - SQLite en local
  - SQLite memoire en test
  - PostgreSQL obligatoire en production
- Calcul RC ASS `rc.request` valide en sandbox.
- Fixture contractuelle du format reel de réponse RC ASS.
- Calcul ASS optionnel sur `POST /api/v1/quotes/{id}/calculate/`.
- Validation des échecs metier ASS `operationStatus` / `status` meme quand
  HTTP renvoie 200.
- Champ `ass_product_data` sur les devis pour stocker les donnees ASS
  spécifiques a un produit avant modelisation metier definitive.
- Endpoint interne authentifie de prévisualisation payload RC :
  - `POST /api/v1/quotes/{id}/ass-payload-preview/`
  - construit le payload ASS par produit sans appel réseau ASS
  - accepte des overrides non persistants pour tester un produit avant calcul
- Endpoint interne authentifie de prévisualisation payload QR :
  - `POST /api/v1/contracts/{id}/ass-payload-preview/`
  - construit le payload d'émission ASS/Diotali sans appeler ASS
  - herite de l'isolation multi-groupe/apporteur du contrat
- Endpoint documentaire contrat :
  - `GET /api/v1/contracts/{id}/documents/`
  - expose `attestation_url` et `carte_brune_url` pour les frontends web/mobile
  - herite de l'isolation multi-groupe/apporteur du contrat
- Commande sandbox protegee :
  - `python manage.py validate_ass_sandbox_issue <contract_id>`
  - affiche le payload d'émission sans appel externe par défaut
  - exige `--confirm-external-ass-call` pour appeler ASS
  - refuse les URLs qui ne ressemblent pas à une sandbox sauf confirmation
    explicite `--allow-non-sandbox-base-url`
  - ne marque pas le contrat comme emis apres l'appel de validation
- Commande sandbox RC protegee :
  - `python manage.py validate_ass_sandbox_quote_calculation <quote_id>`
  - affiche le payload de calcul RC sans appel externe par défaut
  - exige `--confirm-external-ass-call` pour appeler ASS
  - refuse les URLs qui ne ressemblent pas à une sandbox sauf confirmation
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
- Extraction des cles documentaires Diotali vues dans la documentation ASS :
  - `linkAttestation`
  - `linkCarteBrune`
  - `attestationNumber`
  - variantes avec espaces autour des noms de cles
- Emissions sandbox Diotali réelles validées sur contrats `MOTO`, `AUTO` et
  `TRAILER`.
- Fixture contractuelle de réponse QR Diotali :
  - `apps/contracts/tests/fixtures/ass_moto_qrcode_success.json`
  - `apps/contracts/tests/fixtures/ass_auto_qrcode_success.json`
  - `apps/contracts/tests/fixtures/ass_trailer_qrcode_success.json`
- Payloads ASS avances couvertes par tests unitaires locaux :
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
- Phase 15 démarrée :
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
  - `Client` reste une entité metier rattachée a un groupe/apporteur, distincte
    des utilisateurs internes
  - jetons client révocables, rotatifs et hashes via `ClientAccessToken`
  - jetons lies a `Client`, `Contract`, `PartnerGroup` et utilisateur créateur
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
  - notifications client créées lors de la confirmation paiement et de
    l'émission contrat
  - audit logs sur creation, envoi simule, utilisation, revocation et rotation
  - OTP client hashe via `ClientAccessOtp` pour téléchargements sensibles
  - generation OTP mockee via
    `POST /api/v1/client-space/contracts/{id}/documents/otp/`
  - téléchargements attestation/carte brune proteges par `X-Client-OTP`
  - URLs documentaires externes masquées dans l'espace client, remplacées par
    des indicateurs de disponibilité
  - OTP a expiration courte, usage unique, rotation par nouvelle demande et
    verrouillage apres trop d'essais invalides
  - abstraction `ClientMessageProvider` avec provider mock local/test
  - flag `CLIENT_ACCESS_RETURN_SECRETS_IN_RESPONSE` pour retourner les secrets
    bruts seulement en dev/test
  - setting production qui desactive par défaut le retour API des tokens/OTP
    bruts

## Dernier état de tests connu

- Suite complete backend : `214 passed`
- Tests cibles ASS apres ajout Bus ecole et commande RC sandbox : `44 passed`
- Tests cibles paiements phase 15 : `26 passed`
- Tests cibles espace client phase 16 : `24 passed`
- Tests cibles clients/notifications/contrats/paiements apres OTP : `106 passed`
- `manage.py check` : OK
- `makemigrations --check --dry-run` : OK
- `manage.py check --deploy` avec settings production : OK
- CI backend ajoutée dans `.github/workflows/ci.yml`

## Prochaines validations externes

Ces points ne doivent pas etre marques comme termines tant qu'une sandbox reelle
ou un choix provider n'a pas confirme le comportement.

1. ASS `SCHOOL_BUS`, `GARAGE`, `FLEET`
   - Prévisualiser les payloads RC et QR avec les endpoints internes.
   - Executer `validate_ass_sandbox_quote_calculation` sur des devis locaux de
     chaque produit avec `--confirm-external-ass-call`.
   - Executer `validate_ass_sandbox_issue` uniquement sur contrats sandbox dont
     le paiement est confirme et dont l'émission externe est autorisée.
   - Figer une fixture non sensible par réponse réelle acceptee.
2. Bus ecole Postman v1.1
   - Confirmer avec ASS si les champs optionnels de la collection Postman v1.1
     sont acceptes, ignores ou rejetés lorsqu'ils sont presents.
   - Documenter la liste definitive des champs à exposer dans l'API publique.
3. Wave et Orange Money
   - Obtenir les secrets webhook sandbox et configurer les callback URLs vers un
     environnement accessible publiquement.
   - Déclencher un paiement sandbox par provider et verifier signature,
     reference transactionnelle, montant, devise, idempotence et statut final.
   - Ajouter des fixtures provider si le payload reel differe du format local.
4. Espace client
   - Choisir les providers SMS/email avant integration réelle.
   - Brancher l'envoi reel des liens et OTP apres stabilisation du format de
     message client.
   - Conserver le stockage hashe pour les secrets client et OTP.

## Reste à faire

### Phase 13 - Validation emission Diotali

Objectif : valider une vraie réponse d'émission QR/document Diotali sans risquer
de polluer la production.

État : terminée pour la validation générique Diotali, sur emissions sandbox
réelles `MOTO` et `AUTO`.

Fait :

- Base locale SQLite initialisée avec les migrations Django.
- Contrat local de test cree pour prévisualisation :
  - `contract_id=1`
  - produit `MOTO`
- Prévisualiser le payload via
  `POST /api/v1/contracts/{id}/ass-payload-preview/`.
- Prévisualiser ou executer prudemment l'appel sandbox via
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
- Fixture non sensible figée dans
  `apps/contracts/tests/fixtures/ass_moto_qrcode_success.json`.
- Fixture non sensible figée dans
  `apps/contracts/tests/fixtures/ass_auto_qrcode_success.json`.
- Fixture non sensible figée dans
  `apps/contracts/tests/fixtures/ass_trailer_qrcode_success.json`.
- Test contractuel ajoute pour verifier l'extraction depuis la fixture réelle.

Reserve :

- Cette phase valide le format Diotali et les cles documentaires sur un premier
  produit. Les emissions sandbox par produit restent a dérouler dans la phase
  14.

### Phase 14 - Produits ASS avances

Objectif : completer les payloads par produit.

État : démarrée, avec payloads locaux et routage backend couverts par tests.

Fait :

- Auto : flux `rc.request` conserve, options garanties `garantiesOptPT`,
  `garantiesOptAR`, `garantiesOptAS` ajoutées, emission sandbox validée.
- Moto : payloads RC/QR enrichis avec `cylindre`, `usage`, `nombrePlace`.
- Remorque : payload RC exige `referenceVehicule`; payload QR utilise la
  reference fournie dans `ass_product_data`; sandbox confirmee avec la
  `referenceExterne` du tracteur AUTO et RC a `0` pour la premiere remorque.
- Garage : payloads RC/QR gerent `nombreCarte`.
- Bus ecole : produit `SCHOOL_BUS` ajoute cote devis, avec routage RC
  `bus.ecole.rc`, routage QR `bus.ecole.request` et payloads locaux alignes sur
  la documentation ASS fournie.
- Flotte : payload RC accepte `referenceFlotte` et `requests`, avec fallback
  mono-vehicule local.
- Tests payload/routage ajoutes pour calcul RC et emission QR.
- Prévisualisation RC/QR sécurisée ajoutée pour verifier les payloads produits
  avant appel sandbox.
- Commande locale de validation sandbox RC ajoutée pour tester les calculs ASS
  produit sans modifier les devis.

Reste à faire :

- Valider les payloads `GARAGE`, `FLEET`, `SCHOOL_BUS` en sandbox ASS sans
  emission de production.
- Confirmer les champs exacts à exposer dans l'API publique au lieu de garder
  seulement `ass_product_data`.
- Flotte : modéliser proprement le multi-vehicules si le produit doit gérer de
  vraies flottes dans Horus.
- Garage : confirmer les genres metier attendus et la valeur par défaut de
  `nombreCarte`.
- Bus ecole : confirmer en sandbox les genres `BE-VTA` / `BE-VTCATP` et la
  tolerance ASS vis-a-vis des champs optionnels presents dans la collection
  Postman v1.1.

### Phase 15 - Paiements externes

Objectif : passer des paiements modelises aux webhooks reels.

État : socle backend implemente et teste localement ; validation provider
sandbox restante.

Fait :

- Wave webhook.
- Orange Money webhook.
- Verification de signature.
- Idempotence webhook.
- Protection contre rejeu.
- Mise à jour automatique des statuts.
- Tests de securite.

Reste à faire :

- Confirmer avec les contrats providers les noms exacts des champs de reference
  transactionnelle Wave et Orange Money.
- Tester un vrai callback sandbox Wave.
- Tester un vrai callback sandbox Orange Money.
- Ajouter, si necessaire, des adaptateurs de payload par pays/provider si les
  webhooks reels different du format générique documente.

### Phase 16 - Espace client

Objectif : permettre au client final de consulter ses documents.

État : termine pour le backend faisable en dev sans provider externe ; livraison
réelle et interfaces restantes.

Fait :

- Clarifier si `Client` devient un utilisateur connecte ou reste une entité
  rattachée à un apporteur.
- Modele `ClientAccessToken` lie au client, contrat, groupe et créateur.
- Stockage uniquement du hash du jeton.
- Expiration, revocation, utilisation et canal de remise.
- Services de generation, verification, revocation, rotation et renvoi simule.
- API interne admin/apporteur pour créer, révoquer, renouveler et renvoyer un
  lien.
- Endpoint consultation contrats client.
- Téléchargement attestation.
- Téléchargement carte brune.
- Notifications client.
- OTP documents sensibles hashe, expire, usage unique et verrouillable.
- Provider de remise client abstrait avec implementation mock local/test.
- Retour des secrets bruts configurable et desactive par défaut en production.
- Tests de securite : expiration, revocation, autre groupe, rotation, absence de
  stockage clair, refus document sans jeton valide, OTP expire/revoque/usage
  unique/mauvais usage/verrouillage.

Reste à faire :

- Hors dev local : choisir et brancher un vrai provider SMS/email.
- Hors dev local : valider les formats de messages client avec le provider.
- Phase frontend/mobile : ajouter les écrans de consultation client.

### Phase 17 - Frontend Next.js

Objectif : dashboard web.

Contraintes design :

- Interface blanche.
- Police noire lisible.
- Icons professionnelles.
- UI sobre, dense et orientee gestion.

Taches :

- Auth JWT.
- Dashboard admin general.
- Dashboard admin groupe.
- Dashboard apporteur.
- CRUD groupes, utilisateurs, clients, vehicules, devis, contrats.
- Consultation paiements, commissions, audit logs.

### Phase 18 - Mobile Flutter

Objectif : application mobile apporteur/client.

Taches :

- Connexion JWT.
- Creation client.
- Creation vehicule.
- Devis.
- suivi contrat.
- suivi commission.
- Documents attestation/carte brune.

## Risques techniques

- Emission QR réelle ASS/Diotali peut créer une transaction externe.
- Les noms de cles Diotali doivent être confirmes sur une réponse réelle.
- Certains produits ASS demandent encore une modelisation metier definitive ;
  `ass_product_data` est une solution transitoire controlee.
- Les payloads produits avances sont testes localement, mais pas encore valides
  contre une sandbox ASS réelle.
- Les signatures et payloads reels Wave/Orange Money doivent encore être
  confirmes en sandbox provider.
- Les liens et OTP client ne sont pas encore envoyes par vrai provider
  SMS/email.
- Le frontend et le mobile ne sont pas encore crees.

## Regle de maintenance

Apres chaque phase ou intervention significative :

- mettre à jour ce fichier ;
- ajouter les nouvelles fonctionnalités terminées ;
- déplacer les taches terminées hors du reste a faire ;
- noter les tests executes et leur resultat ;
- noter les risques ou points bloquants restants.
