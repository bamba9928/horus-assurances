# Project Roadmap

Ce fichier sert de fil conducteur du projet Horus Assurances. Il doit etre mis a
jour a chaque phase importante, apres les changements de code et les tests.

## Etat actuel

Backend Django REST Framework avance jusqu'a la phase 12.

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
- Routage emission QR par type de produit :
  - `AUTO`
  - `MOTO`
  - `FLEET`
  - `TRAILER`
  - `GARAGE`
- Champs documentaires Diotali :
  - `attestation_url`
  - `carte_brune_url`
- CI GitHub Actions pour le backend :
  - `manage.py check`
  - `makemigrations --check --dry-run`
  - `pytest`
  - `manage.py check --deploy`

## Dernier etat de tests connu

- Suite complete backend : `149 passed`
- `manage.py check` : OK
- `manage.py check --deploy` avec settings production : OK
- `makemigrations --check --dry-run` : OK
- CI backend ajoutee dans `.github/workflows/ci.yml`

## Reste a faire

### Phase 13 - Validation emission Diotali

Objectif : valider une vraie reponse d'emission QR/document Diotali sans risquer
de polluer la production.

Taches :

- Creer ou identifier un contrat sandbox de test.
- Appeler l'emission QR reelle uniquement avec validation explicite.
- Capturer la reponse non sensible.
- Figer une fixture contractuelle.
- Confirmer les cles exactes pour :
  - attestation
  - carte brune
- Ajuster l'extraction si necessaire.

### Phase 14 - Produits ASS avances

Objectif : completer les payloads par produit.

Taches :

- Auto : consolider le flux existant.
- Moto : verifier les champs `cylindre`, `usage`, `nombrePlace`.
- Remorque : verifier `referenceVehicule` et champs requis.
- Garage : verifier `nombreCarte`, genre et garanties.
- Flotte : verifier le format multi-items.
- Ajouter les tests payload par produit.

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
- Certains produits ASS demandent des champs metier non modelises.
- Les webhooks paiement ne sont pas encore implementes.
- Le frontend et le mobile ne sont pas encore crees.

## Regle de maintenance

Apres chaque phase ou intervention significative :

- mettre a jour ce fichier ;
- ajouter les nouvelles fonctionnalites terminees ;
- deplacer les taches terminees hors du reste a faire ;
- noter les tests executes et leur resultat ;
- noter les risques ou points bloquants restants.
