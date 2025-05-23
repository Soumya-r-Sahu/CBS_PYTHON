# 🖥️ frontend integration

Easily connect your app to the CBS Banking API! This guide covers basics, CORS, and quick starts for popular frameworks.

| 🌐 Frameworks      | 🛡️ Auth | 📦 Data | ⚠️ Errors | 🔗 Example |
|-------------------|---------|---------|-----------|-----------|
| Django            | JWT     | JSON    | Codes     | [link](#django) |
| React/Next.js     | JWT     | JSON    | Codes     | [link](#react)  |
| Angular           | JWT     | JSON    | Codes     | [link](#angular) |
| Vue.js            | JWT     | JSON    | Codes     | [link](#vue) |
| Flutter           | JWT     | JSON    | Codes     | [link](#flutter) |
| Native (iOS/Android) | JWT  | JSON    | Codes     | [link](#native) |

## 🚀 basics
- **Base URL:** `http://<host>:<port>/api/v1`
- **Auth:** Bearer JWT
- **Content-Type:** JSON
- **Errors:** Standard codes

## 🔒 cors
- Allowed origins: `CBS_CORS_ALLOWED_ORIGINS`
- Methods: GET, POST, PUT, DELETE, PATCH, OPTIONS
- Headers: Authorization, Content-Type, etc.
- Credentials: Supported

## ⚡ quick start
### django
```python
from Backend.integration_interfaces.django_client import BankingAPIClient
```
### react
```js
fetch('/api/v1/accounts', { headers: { Authorization: 'Bearer <token>' } })
```
### angular
```ts
this.http.get('/api/v1/accounts', { headers: { Authorization: 'Bearer <token>' } })
```
### vue
```js
axios.get('/api/v1/accounts', { headers: { Authorization: 'Bearer <token>' } })
```
### flutter
```dart
http.get(Uri.parse('/api/v1/accounts'), headers: { 'Authorization': 'Bearer <token>' })
```
### native
Use your platform's HTTP client with JWT Bearer auth.

## 📚 more
- [API standards](../standards.md)
- [Integration overview](./README.md)
- [Versioning](../versioning/README.md)
