# Project Roadmap

Ce fichier sert de fil conducteur du projet Horus Assurances. Il doit etre mis a
jour a chaque phase importante, apres les changements de code et les tests.

## Etat actuel

Backend Django REST Framework avance jusqu'a la phase 14 partielle cote
integration ASS.

Stack cible :

- Backend : Django + Django REST Framework
- Base locale : SQLite
- Base production : PostgreSQL
- Authentification : JWT
- Web : Next.js / React
- Mobile : Flutter

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
- Commande sandbox protegee :
  - `python manage.py validate_ass_sandbox_issue <contract_id>`
  - affiche le payload d'emission sans appel externe par defaut
  - exige `--confirm-external-ass-call` pour appeler ASS
  - refuse les URLs qui ne ressemblent pas a une sandbox sauf confirmation
    explicite `--allow-non-sandbox-base-url`
  - ne marque pas le contrat comme emis apres l'appel de validation
- Routage du calcul RC ASS par type de produit :
  - `AUTO` -> `rc.request`
  - `MOTO` -> `rc.moto`
  - `FLEET` -> `rc.flotte.request`
  - `TRAILER` -> `remorque.rc.request`
  - `GARAGE` -> `rc.garage`
- Routage emission QR par type de produit :
  - `AUTO`
  - `MOTO`
  - `FLEET`
  - `TRAILER`
  - `GARAGE`
- Champs documentaires Diotali :
  - `attestation_url`
  - `carte_brune_url`
- Extraction des cles documentaires Diotali vues dans la documentation ASS :
  - `linkAttestation`
  - `linkCarteBrune`
  - `attestationNumber`
  - variantes avec espaces autour des noms de cles
- Payloads ASS avances couverts par tests unitaires locaux :
  - Moto : `cylindre`, `usage`, `nombrePlace`
  - Remorque : `referenceVehicule`
  - Garage : `nombreCarte`
  - Flotte : `referenceFlotte` et `requests`
- CI GitHub Actions pour le backend :
  - `manage.py check`
  - `makemigrations --check --dry-run`
  - `pytest`
  - `manage.py check --deploy`

## Dernier etat de tests connu

- Suite complete backend : `169 passed`
- `manage.py check` : OK
- `makemigrations --check --dry-run` : OK
- `manage.py check --deploy` avec settings production : OK
- CI backend ajoutee dans `.github/workflows/ci.yml`

## Reste a faire

### Phase 13 - Validation emission Diotali

Objectif : valider une vraie reponse d'emission QR/document Diotali sans risquer
de polluer la production.

Etat : non terminee. Les prevalidations locales sont en place, mais aucune
emission sandbox reelle non sensible n'a encore ete capturee.

Taches :

- Creer ou identifier un contrat sandbox de test.
- Previsualiser le payload via
  `POST /api/v1/contracts/{id}/ass-payload-preview/`.
- Previsualiser ou executer prudemment l'appel sandbox via
  `python manage.py validate_ass_sandbox_issue <contract_id>`.
- Appeler l'emission QR reelle uniquement avec validation explicite.
- Capturer la reponse non sensible.
- Figer une fixture contractuelle.
- Confirmer les cles exactes pour :
  - attestation
  - carte brune
- Ajuster l'extraction si necessaire apres reponse sandbox reelle.

Avancement local :

- Les cles documentees `linkAttestation`, `linkCarteBrune` et
  `attestationNumber` sont prises en charge par l'extraction locale.
- Les endpoints de previsualisation permettent de verifier les payloads sans
  consommer de QR code ni creer d'attestation externe.
- La commande `validate_ass_sandbox_issue` permet de preparer l'appel sandbox et
  d'effectuer l'appel avec double garde-fou, sans persister l'emission.
- Il reste a confirmer ces cles sur une vraie emission sandbox non sensible.

### Phase 14 - Produits ASS avances

Objectif : completer les payloads par produit.

Etat : demarree, avec payloads locaux et routage backend couverts par tests.

Fait :

- Auto : flux `rc.request` conserve.
- Moto : payloads RC/QR enrichis avec `cylindre`, `usage`, `nombrePlace`.
- Remorque : payload RC exige `referenceVehicule`; payload QR peut utiliser la
  reference fournie dans `ass_product_data`.
- Garage : payloads RC/QR gerent `nombreCarte`.
- Flotte : payload RC accepte `referenceFlotte` et `requests`, avec fallback
  mono-vehicule local.
- Tests payload/routage ajoutes pour calcul RC et emission QR.
- Previsualisation RC/QR securisee ajoutee pour verifier les payloads produits
  avant appel sandbox.

Reste a faire :

- Valider ces payloads en sandbox ASS sans emission de production.
- Confirmer les champs exacts a exposer dans l'API publique au lieu de garder
  seulement `ass_product_data`.
- Flotte : modeliser proprement le multi-vehicules si le produit doit gerer de
  vraies flottes dans Horus.
- Garage : confirmer les genres metier attendus et la valeur par defaut de
  `nombreCarte`.

### Phase 15 - Paiements externes

Objectif : passer des paiements modelises aux webhooks reels.

Taches :

- Wave webhook.
- Orange Money webhook.
- Verification de signature.
- Idempotence webhook.
- Protection contre rejeu.
- Mise a jour automatique des statuts.
- Tests de securite.

### Phase 16 - Espace client

Objectif : permettre au client final de consulter ses documents.

Taches :

- Clarifier si `Client` devient un utilisateur connecte ou reste une entite
  rattachee a un apporteur.
- Endpoint consultation contrats client.
- Telechargement attestation.
- Telechargement carte brune.
- Notifications client.

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
- Les webhooks paiement ne sont pas encore implementes.
- Le frontend et le mobile ne sont pas encore crees.

## Regle de maintenance

Apres chaque phase ou intervention significative :

- mettre a jour ce fichier ;
- ajouter les nouvelles fonctionnalites terminees ;
- deplacer les taches terminees hors du reste a faire ;
- noter les tests executes et leur resultat ;
- noter les risques ou points bloquants restants.
