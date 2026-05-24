# Project Roadmap

Ce fichier sert de fil conducteur du projet Horus Assurances. Il doit etre mis a
jour a chaque phase importante, apres les changements de code et les tests.

## Etat actuel

Backend Django REST Framework avance jusqu'a la phase 16 cote backend. Les
socles locaux des phases 15 et 16 sont implementes et testes ; les validations
externes et interfaces restent a finaliser.

Stack cible :

- Backend : Django + Django REST Framework
- Base locale : SQLite
- Base production : PostgreSQL
- Authentification : JWT
- Web : Next.js / React
- Mobile : Flutter

## Synthese des phases

- Phase 13 : terminee pour la validation generique Diotali, avec emissions
  sandbox reelles `MOTO`, `AUTO` et `TRAILER`.
- Phase 14 : backend produits avances implemente localement ; validations
  sandbox reelles `GARAGE`, `FLEET` et `SCHOOL_BUS` encore a faire.
- Phase 15 : socle webhooks paiement implemente et teste localement ; callbacks
  sandbox Wave et Orange Money encore a valider avec les providers.
- Phase 16 : socle backend espace client implemente et teste localement ;
  livraison reelle SMS/email, OTP et interfaces frontend/mobile encore a faire.
- Phase 17 : non demarree.
- Phase 18 : non demarree.

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
- Endpoint interne authentifie de previsualisation payload QR :
  - `POST /api/v1/contracts/{id}/ass-payload-preview/`
  - construit le payload d'emission ASS/Diotali sans appeler ASS
  - herite de l'isolation multi-groupe/apporteur du contrat
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
  - Bus Ecole : champs vehicule standards, `nombrePlace`, `puissanceFiscale`
  - Garage : `nombreCarte`
  - Flotte : `referenceFlotte` et `requests`
- CI GitHub Actions pour le backend :
  - `manage.py check`
  - `makemigrations --check --dry-run`
  - `pytest`
  - `manage.py check --deploy`
- Phase 15 demarree :
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

## Dernier etat de tests connu

- Suite complete backend : `205 passed`
- Tests cibles ASS apres ajout Bus Ecole et commande RC sandbox : `44 passed`
- Tests cibles paiements phase 15 : `26 passed`
- Tests cibles espace client phase 16 : `84 passed`
- `manage.py check` : OK
- `makemigrations --check --dry-run` : OK
- `manage.py check --deploy` avec settings production : OK
- CI backend ajoutee dans `.github/workflows/ci.yml`

## Prochaines validations externes

Ces points ne doivent pas etre marques comme termines tant qu'une sandbox reelle
ou un choix provider n'a pas confirme le comportement.

1. ASS `SCHOOL_BUS`, `GARAGE`, `FLEET`
   - Previsualiser les payloads RC et QR avec les endpoints internes.
   - Executer `validate_ass_sandbox_quote_calculation` sur des devis locaux de
     chaque produit avec `--confirm-external-ass-call`.
   - Executer `validate_ass_sandbox_issue` uniquement sur contrats sandbox dont
     le paiement est confirme et dont l'emission externe est autorisee.
   - Figer une fixture non sensible par reponse reelle acceptee.
2. Bus Ecole Postman v1.1
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
   - Ajouter OTP pour les actions sensibles apres stabilisation de la remise du
     lien client.
   - Conserver le stockage hashe pour les secrets client et OTP.

## Reste a faire

### Phase 13 - Validation emission Diotali

Objectif : valider une vraie reponse d'emission QR/document Diotali sans risquer
de polluer la production.

Etat : terminee pour la validation generique Diotali, sur emissions sandbox
reelles `MOTO` et `AUTO`.

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
- Remorque : payload RC exige `referenceVehicule`; payload QR utilise la
  reference fournie dans `ass_product_data`; sandbox confirmee avec la
  `referenceExterne` du tracteur AUTO et RC a `0` pour la premiere remorque.
- Garage : payloads RC/QR gerent `nombreCarte`.
- Bus Ecole : produit `SCHOOL_BUS` ajoute cote devis, avec routage RC
  `bus.ecole.rc`, routage QR `bus.ecole.request` et payloads locaux alignes sur
  la documentation ASS fournie.
- Flotte : payload RC accepte `referenceFlotte` et `requests`, avec fallback
  mono-vehicule local.
- Tests payload/routage ajoutes pour calcul RC et emission QR.
- Previsualisation RC/QR securisee ajoutee pour verifier les payloads produits
  avant appel sandbox.
- Commande locale de validation sandbox RC ajoutee pour tester les calculs ASS
  produit sans modifier les devis.

Reste a faire :

- Valider les payloads `GARAGE`, `FLEET`, `SCHOOL_BUS` en sandbox ASS sans
  emission de production.
- Confirmer les champs exacts a exposer dans l'API publique au lieu de garder
  seulement `ass_product_data`.
- Flotte : modeliser proprement le multi-vehicules si le produit doit gerer de
  vraies flottes dans Horus.
- Garage : confirmer les genres metier attendus et la valeur par defaut de
  `nombreCarte`.
- Bus Ecole : confirmer en sandbox les genres `BE-VTA` / `BE-VTCATP` et la
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

Etat : socle backend MVP implemente et teste localement ; livraison reelle et
interfaces restantes.

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
- Tests de securite : expiration, revocation, autre groupe, rotation, absence de
  stockage clair et refus document sans jeton valide.

Reste a faire :

- Brancher un vrai provider SMS/email apres validation du format de message.
- Ajouter OTP pour les actions sensibles comme le telechargement attestation ou
  carte brune.
- Ajouter les ecrans frontend/mobile de consultation client.

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
- Suivi contrat.
- Suivi commission.
- Documents attestation/carte brune.

## Risques techniques

- Emission QR reelle ASS/Diotali peut creer une transaction externe.
- Les noms de cles Diotali doivent etre confirmes sur une reponse reelle.
- Certains produits ASS demandent encore une modelisation metier definitive ;
  `ass_product_data` est une solution transitoire controlee.
- Les payloads produits avances sont testes localement mais pas encore valides
  contre une sandbox ASS reelle.
- Les signatures et payloads reels Wave/Orange Money doivent encore etre
  confirmes en sandbox provider.
- Les liens client ne sont pas encore envoyes par vrai provider SMS/email.
- L'OTP pour les telechargements sensibles reste a ajouter.
- Le frontend et le mobile ne sont pas encore crees.

## Regle de maintenance

Apres chaque phase ou intervention significative :

- mettre a jour ce fichier ;
- ajouter les nouvelles fonctionnalites terminees ;
- deplacer les taches terminees hors du reste a faire ;
- noter les tests executes et leur resultat ;
- noter les risques ou points bloquants restants.
