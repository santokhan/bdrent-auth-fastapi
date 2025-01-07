## OTP Messages

```py
OTP = 123456
message = f"Your verification code is: {OTP}."
```

## Test

```sh
curl -X 'POST' \
  'http://localhost:8002/api/v1/otp/generate-otp/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"phone_number": "01307230077"}'
```

```sh
curl -X 'POST' \
  'http://localhost:8002/api/v1/otp/verify-otp/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{"phone_number": "01307230077", "OTP": ""}'
```