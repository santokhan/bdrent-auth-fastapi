# Test

```sh
curl -X 'POST' \
  'http://localhost:8002/api/v1/auth/signup' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "john_doe",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "01307230077",
  "password": "secureP@ss123"
}
'
```