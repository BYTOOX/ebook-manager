# SPEC — Migration auth Bearer pour Aurelia

## Contexte

Le backend Aurelia utilise actuellement une authentification par cookie HTTP-only.

Pour l'application Android native, le choix produit est de migrer vers une authentification Bearer token pour tous les clients :

- frontend web
- app Android
- futurs clients API

## Objectif

Remplacer le modèle cookie par un modèle Bearer token uniforme.

Toutes les routes protégées doivent lire :

```http
Authorization: Bearer <token>
```

## Comportement cible

### Login

Route existante :

```txt
POST /api/v1/auth/login
```

Elle doit retourner un JSON :

```json
{
  "ok": true,
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 2592000,
  "user": {
    "id": "...",
    "username": "admin",
    "display_name": "Aurelia"
  }
}
```

Elle ne doit plus poser de cookie.

### Setup premier utilisateur

Route existante :

```txt
POST /api/v1/auth/setup
```

Elle doit aussi retourner un token Bearer après création du premier utilisateur.

### Me

```txt
GET /api/v1/auth/me
```

Doit fonctionner uniquement avec :

```http
Authorization: Bearer <token>
```

### Logout

```txt
POST /api/v1/auth/logout
```

En V1 stateless, cette route peut retourner :

```json
{ "ok": true }
```

Le frontend et l'application Android supprimeront le token localement.

## Backend attendu

### `create_session_token`

La fonction existante peut être conservée si elle produit déjà un JWT valide avec :

- `sub`
- `exp`

Renommer en `create_access_token` est optionnel, mais recommandé pour clarté.

### `decode_session_token`

Peut être conservée ou renommée en `decode_access_token`.

### Dépendance `get_current_user`

Elle doit :

1. lire le header `Authorization`
2. vérifier que le schéma est `Bearer`
3. décoder le JWT
4. récupérer l'utilisateur en base
5. retourner une erreur 401 si invalide

Elle ne doit plus dépendre du cookie.

Erreur attendue :

```python
HTTPException(
    status_code=401,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)
```

## Frontend web attendu

Le frontend React doit :

- stocker `access_token` après login
- envoyer `Authorization: Bearer <token>` sur toutes les requêtes API protégées
- supprimer le token au logout
- rediriger vers login si 401
- ne plus dépendre de `credentials: include` pour l'auth

Stockage V1 accepté :

- localStorage

Point sécurité documenté :

- Bearer en localStorage est acceptable pour cette application personnelle auto-hébergée V1
- HTTPS obligatoire en production
- CSP recommandée

## Critères d'acceptation

- login web fonctionne
- setup premier utilisateur fonctionne
- `/auth/me` fonctionne avec Bearer
- `/books` fonctionne avec Bearer
- une requête sans token retourne 401
- une requête avec token invalide retourne 401
- le frontend web fonctionne après refresh page
- les tests backend passent
- le build frontend passe
- README mis à jour avec la nouvelle auth
