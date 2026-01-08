# Décisions de design - Base de données

## categorization_rules

Table qui stocke des règles en langage naturel que l'IA consomme pour catégoriser les transactions.

**Exemples de règles :**

| rule |
|------|
| COUCHE-TARD, ACCOMMODATION M M : si montant >= 50$ → Carburant, sinon → Cochonneries |
| FIZZ : 13$ → Téléphone, 33$ → Internet |
| STH suivi d'un numéro = St-Hubert → Restaurants |
| PAUS SAGUENAY = spa → Divers - Autres |
| SAVANA = centre d'amusement pour enfants → Bébé |
| Transactions dans la ville de Québec lors d'un séjour → Vacances |

**Utilisation dans le prompt :**
```
Voici les règles de catégorisation à appliquer :
{règles de la table}

Voici les catégories disponibles :
{liste des catégories}

Catégorise cette transaction :
{transaction}
```

## categorization_rules.account_id

`NULL` = la règle s'applique à tous les comptes.

Si une valeur est spécifiée, la règle s'applique uniquement à ce compte. Utile si un même marchand doit être catégorisé différemment selon le compte.