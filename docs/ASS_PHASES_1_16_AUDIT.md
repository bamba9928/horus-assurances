# Audit phases 1 a 16 vs documentation ASS

Date de verification : 2026-05-25

## Sources verifiees

- Roadmap projet : `docs/PROJECT_ROADMAP.md`
- Code backend : `backend/apps/*`, `backend/config/urls.py`
- Collection ASS Postman v1.1 :
  `C:\Users\TBE\OneDrive\Documents\ASS DOCUMENTATION\ASS API PARTNER v1.1`
- PDF ASS v1.0 :
  `C:\Users\TBE\OneDrive\Documents\ASS DOCUMENTATION\ASS_API_Integration-v1.0.pdf`
- Note auth ASS :
  `C:\Users\TBE\OneDrive\Documents\ASS DOCUMENTATION\L'authentification se fait avec Bas.txt`
- ZIP ASS :
  `C:\Users\TBE\OneDrive\Documents\ASS DOCUMENTATION\Documentation_API_A.S.S.zip`

Pas d'appel sandbox externe effectue pendant cet audit.

## Synthese

Le backend est coherent avec la documentation ASS pour le socle integre en dev :
Basic Auth, endpoints principaux RC/QR, payloads par produit, journalisation,
gestion `operationStatus`, extraction `linkAttestation` et `linkCarteBrune`.

Les phases 1 a 12 sont maintenant formalisees dans le roadmap. Elles restent
verifiees par fonctionnalites livrees, car leur historique initial n'existait
pas comme sections nommees. Les phases 13 a 16 sont tracees explicitement dans
le roadmap.

Statut global :

- Phases 1 a 12 : OK cote backend local, non directement ASS sauf integration
  preparee.
- Phase 13 : OK pour `AUTO`, `MOTO`, `TRAILER` en sandbox reelle deja figee par
  fixtures ; reste a ne pas requalifier cette phase comme validation de tous les
  produits.
- Phase 14 : conforme localement a la collection ASS v1.1 pour les payloads
  attendus ; validations sandbox reelles encore requises pour `SCHOOL_BUS`,
  `GARAGE`, `FLEET`.
- Phase 15 : hors documentation ASS, depend des providers Wave/Orange ; socle
  backend local OK, sandbox providers restante.
- Phase 16 : hors documentation ASS ; backend/dev termine, provider SMS/email et
  interfaces hors perimetre local.

## Verification phases 1 a 16

| Phase | Perimetre verifie | Statut | Comparaison ASS |
| --- | --- | --- | --- |
| 1 | Architecture Django/DRF, apps backend, settings | OK | Non applicable ASS |
| 2 | Auth JWT interne, user custom, roles | OK | ASS utilise Basic Auth separee pour appels externes |
| 3 | Groupes partenaires et isolation multi-groupe | OK | Non applicable ASS |
| 4 | Clients et vehicules | OK | Alimente les champs `assure`, `souscripteur`, `vehicule` |
| 5 | Devis, montants, options garanties | OK | Aligne avec `rc.request` et options `garanties*` |
| 6 | Paiements, wallets, statuts | OK | Fournit `referenceTrxPartner` et precondition emission |
| 7 | Contrats | OK | Supporte emission QR ASS/Diotali |
| 8 | Commissions | OK | Non applicable ASS |
| 9 | Audit, notifications, dashboard | OK | Journalise appels ASS et evenements contrat |
| 10 | Client ASS, logs, Basic Auth | OK | Conforme a la note Basic Auth et au PDF |
| 11 | Calcul RC mono ASS | OK | `rc.request` implemente et fixture sandbox RC presente |
| 12 | Emission QR mono preparee | OK | `qrcode.request` implemente, extraction documents OK |
| 13 | Validation Diotali sandbox | OK partiel produit | Sandbox reelle validee pour `MOTO`, `AUTO`, `TRAILER` |
| 14 | Produits ASS avances | OK local, sandbox restante | `MOTO`, `TRAILER`, `FLEET`, `SCHOOL_BUS`, `GARAGE` routes/payloads couverts |
| 15 | Webhooks paiement externes | OK local | Hors documentation ASS |
| 16 | Espace client securise | OK backend/dev | Hors documentation ASS |

## Endpoints ASS compares

| Endpoint documentation ASS | Backend | Statut |
| --- | --- | --- |
| `POST /api/v1/partner/rc.request` | `ASSAPIClient.calculate_rc` | OK |
| `POST /api/v1/partner/qrcode.request` | `ASSAPIClient.request_qrcode` | OK |
| `POST /api/v1/partner/rc.moto` | `ASSAPIClient.calculate_moto_rc` | OK |
| `POST /api/v1/partner/moto.request` | `ASSAPIClient.request_moto_qrcode` | OK |
| `POST /api/v1/partner/rc.flotte.request` | `ASSAPIClient.calculate_fleet_rc` | OK local |
| `POST /api/v1/partner/qrcode.flotte.request` | `ASSAPIClient.request_fleet_qrcode` | OK local, modele metier multi-vehicules restant |
| `POST /api/v1/partner/remorque.rc.request` | `ASSAPIClient.calculate_trailer_rc` | OK |
| `POST /api/v1/partner/remorque.qrcode.request` | `ASSAPIClient.request_trailer_qrcode` | OK, sandbox reelle validee |
| `POST /api/v1/partner/bus.ecole.rc` | `ASSAPIClient.calculate_school_bus_rc` | OK local, sandbox restante |
| `POST /api/v1/partner/bus.ecole.request` | `ASSAPIClient.request_school_bus_qrcode` | OK local, sandbox restante |
| `POST /api/v1/partner/rc.garage` | `ASSAPIClient.calculate_garage_rc` | OK local, sandbox restante |
| `POST /api/v1/partner/garage.request` | `ASSAPIClient.request_garage_qrcode` | OK local, sandbox restante |
| `POST /api/v1/partner/stock.qr` | `ASSAPIClient.get_qrcode_stock` | Client bas niveau OK ; non expose metier par choix produit |
| `POST /api/v1/partner/qrcode.cancel` | `ASSAPIClient.cancel_qrcode` | Client bas niveau OK ; non expose metier |
| `POST /api/v1/partner/verif.immatriculation` | `ASSAPIClient.verify_registration` | Client bas niveau OK ; non expose metier |
| `POST /api/v1/promobile/check.qrcode.status` | `ASSAPIClient.check_qrcode_status` | Client bas niveau OK ; non expose metier |

Note : le PDF v1.0 mentionne `stock.qr` comme `GET` sans body, alors que la
collection Postman v1.1 le fournit en `POST` avec `code`. Le backend suit la
collection v1.1 dans le client bas niveau, mais Horus ne doit pas exposer le
stock QR : il reste gere dans le compte ASS natif.

## Payloads ASS par produit

| Produit | Documentation ASS v1.1 | Backend | Ecart |
| --- | --- | --- | --- |
| AUTO/mono RC | `puissanceFiscale`, `duree`, `genre`, `nombrePlace`, `periodicite`, `energie`, valeurs, `garanties`, options, `cout_police`, `remise_rc` | `build_ass_rc_payload` | OK |
| AUTO/mono QR | `assure`, `souscripteur`, `vehicule`, `police`, `dateEffet`, `periodicite`, `typePersonne`, `referenceTrxPartner`, `responsabiliteCivile`, garanties | `build_ass_qrcode_payload` | OK ; sandbox reelle AUTO validee |
| MOTO RC | `cylindre`, `duree`, `periodicite`, `genre`, `energie`, `usage`, `nombrePlace`, `cout_police`, `remise_rc`, `garanties` | `build_ass_moto_rc_payload` | OK |
| MOTO QR | `vehicule.cylindre`, `vehicule.usage`, infos assure/souscripteur | `build_ass_moto_qrcode_payload` | OK ; sandbox reelle MOTO validee |
| REMORQUE RC | `duree`, `periodicite`, `referenceVehicule` | `build_ass_trailer_rc_payload` | OK |
| REMORQUE QR | `referenceVehicule`, `immatriculation`, `marque`, `modele`, `responsabiliteCivile`, assure/souscripteur | `build_ass_trailer_qrcode_payload` | OK ; sandbox reelle TRAILER validee |
| FLEET RC | `referenceFlotte`, `periodicite`, `duree`, `dateEffet`, `requests[]` | `build_ass_fleet_rc_payload` | OK local ; vrai multi-vehicules a modeliser |
| FLEET QR | `referenceFlotte`, `items[]` multi-vehicules | `build_ass_fleet_qrcode_payload` | Partiel : un seul item depuis le contrat courant |
| SCHOOL_BUS RC | `duree`, `energie`, `periodicite`, `genre`, `nombrePlace`, `puissanceFiscale`, valeurs, `garanties` | `build_ass_school_bus_rc_payload` | OK local ; sandbox restante |
| SCHOOL_BUS QR | flat fields + `vehicule` + valeurs/garanties | `build_ass_school_bus_qrcode_payload` | OK local ; tolerance champs optionnels a confirmer |
| GARAGE RC | `duree`, `periodicite`, `genre`, `nombreCarte`, valeurs, `garanties` | `build_ass_garage_rc_payload` | OK local ; sandbox restante |
| GARAGE QR | `nombreCarte`, `immatriculation`, `genre`, valeurs, `garanties`, assure/souscripteur | `build_ass_garage_qrcode_payload` | OK local ; sandbox restante |

## Reponses ASS

Points alignes :

- Le PDF precise qu'un HTTP 200/201/202 ne suffit pas : `operationStatus` doit
  etre `SUCCESS`. Le backend traite `operationStatus` et `status`.
- Les liens documentaires `linkAttestation` et `linkCarteBrune` sont extraits et
  stockes dans `attestation_url` et `carte_brune_url`.
- Les fixtures reelles `AUTO`, `MOTO`, `TRAILER` confirment ces cles.

Points a surveiller :

- Le PDF v1.0 et la collection v1.1 divergent sur certains noms historiques
  (`qrcode.cancel` vs libelle PDF mono cancel). La divergence `stock.qr`
  GET/POST est notee, mais hors workflow Horus.
- Le champ `secureKey` est documente comme a ignorer ; le backend ne l'exploite
  pas, ce qui est coherent.
- La collection Moto contient une incoherence de valeur d'usage entre RC et QR
  (`NON_COMMERCIAL` / `NON_COMMERCIALE`). Le backend laisse la valeur venir de
  `ass_product_data`, donc la valeur definitive doit etre confirmee en sandbox.

## Ecarts et actions restantes

1. `FLEET` QR : le backend sait construire un payload flotte, mais le modele
   metier Horus ne gere pas encore une vraie liste de vehicules dans un contrat
   flotte. A faire avant usage production flotte.
2. `SCHOOL_BUS` : le payload local reprend les champs Postman v1.1, mais la
   tolerance ASS des champs optionnels doit etre confirmee en sandbox.
3. `GARAGE`, `FLEET`, `SCHOOL_BUS` : validations sandbox reelles encore a faire.
4. `stock.qr` : client bas niveau present, mais aucun endpoint metier Horus a
   ajouter. Le stock QR reste gere dans le compte ASS natif.
5. `qrcode.cancel`, `verif.immatriculation`, `check.qrcode.status` : clients bas
   niveau presents, mais pas d'endpoints metier Horus. Ce n'est pas bloquant
   pour phases 1 a 16, mais a planifier seulement si le back-office doit gerer
   annulation, verification ou statut QR.
6. Documentation projet : les phases 1 a 12 sont formalisees dans le roadmap ;
   conserver cette structure pour les prochains audits.

## Conclusion

Le backend phases 1 a 16 est coherent avec la documentation ASS pour le
perimetre implemente et testable localement. Les reserves restantes sont des
validations externes ou des choix produit : sandbox ASS avancee, vraie flotte
multi-vehicules, endpoints auxiliaires ASS a exposer ou non hors stock QR, et
providers externes hors ASS.
