# EARS Specification

> Auteur : business-analyst. Validateur : product-owner. Approbateur humain : CP1.
> Le BA est l'unique auteur de la spécification EARS finale. Le PO fournit et valide la valeur métier, mais ne réécrit pas la spec. Remplacer les consignes par du contenu propre à la story.

## Valeur métier (PO)

- **Why — problème / valeur attendue :**
- **For whom — utilisateur/persona cible :**
- **Success metrics — mesure du succès :**
- **Priorité (P0/P1/P2) :**
- **Scope haut niveau — in scope :**
- **Scope haut niveau — out of scope :**

## Spécification (BA)

### Contexte

- **Story ID :**
- **Acteurs et environnement :**
- **Hypothèses :**
- **Dépendances :**
- **Glossaire :**
- **Questions ouvertes :**

### Exigences fonctionnelles (EARS)

Écrire chaque exigence sous forme EARS testable :
- **Event-driven :** `When <trigger>, the system shall <behavior>.`
- **State-driven :** `While <state>, the system shall <behavior>.`
- **Condition :** `If <condition>, then the system shall <behavior>.`

Exemples (à remplacer) :
- When a user submits valid credentials, the system shall create an authenticated session.
- If a payment is declined, then the system shall display a clear failure message and preserve the cart.
- While an account is locked, the system shall reject authentication attempts.

#### Exigences de la story

- EARS-01:
- EARS-02:

### Contraintes non fonctionnelles

Consigner les contraintes mesurables pertinentes (performance, disponibilité, accessibilité, confidentialité, sécurité, compatibilité, observabilité et limites opérationnelles).

- NFR-01:
- NFR-02:

### Workflows et cas limites

- Happy path :
- Alternate paths :
- Edge cases :

### Critères d'acceptation (Gherkin)

Utiliser des scénarios Given/When/Then observables liés aux identifiants d'exigence.

```gherkin
Feature: <capability>

  Scenario: <observable outcome>
    Given <initial context>
    When <trigger or action>
    Then <expected result>
```

### Matrice de traçabilité requirement → test

| Requirement ID | Critère / scénario Gherkin | Test ID |
| --- | --- | --- |
| EARS-01 | | |

### Hors périmètre

Lister les comportements et changements explicitement exclus de cette story.

-
