# Firebase Identity Platform MFA rollout checklist

This guide is an operator checklist. It does not enable MFA by itself and does not store Firebase secrets in the repository.

## Current decision

- First factor: existing Firebase email/password authentication.
- Preferred second factor: Firebase Identity Platform TOTP (authenticator app).
- Factor secret ownership: Firebase Identity Platform only; never persist TOTP shared secrets in Nexora tables, logs, analytics, or crash reports.
- Nexora authorization: Django verifies the Firebase ID token and trusts only the reserved `firebase.sign_in_second_factor` claim.
- Recovery: users should enroll a second independent factor or follow a documented support recovery process before MFA is made mandatory. Nexora recovery codes are not implemented.

## Project configuration prerequisites

1. Confirm the target Firebase project and its billing/Identity Platform requirements with the project owner.
2. Upgrade Firebase Authentication to Google Cloud Identity Platform in the Firebase/Google Cloud console.
3. In Identity Platform, enable TOTP multi-factor authentication for the project.
4. Keep email/password enabled as the first factor.
5. Require verified email before allowing a user to enroll TOTP.
6. Configure the project's allowed sign-in providers and monitoring before enabling MFA for production users.
7. Do not enable an organization-wide mandatory MFA policy until the app's enrollment, sign-in challenge, second-factor recovery, and support workflows have been tested.

TOTP MFA is documented for the modular Firebase JavaScript SDK. The mobile app uses that SDK, but the Expo native development build must still pass the end-to-end proof of concept before production rollout.

## Required mobile behavior

### Enrollment

1. Require a current authenticated user and verified email.
2. Reauthenticate the first factor before beginning enrollment.
3. Request a Firebase multi-factor session.
4. Generate a Firebase TOTP secret.
5. Display the QR code or a one-time manual setup key. Never log or persist the secret.
6. Ask the user to enter a current six-digit authenticator code.
7. Finalize enrollment through Firebase's TOTP enrollment assertion.
8. Force-refresh the Firebase ID token and call `GET /api/v1/account/me/`.
9. Confirm the backend reports `mfa_verified=true` only after a fresh MFA sign-in; enrollment alone must not be presented as proof that the current session used MFA.

### Sign-in challenge

1. Attempt the normal Firebase first-factor sign-in.
2. Handle `auth/multi-factor-auth-required` without navigating to the authenticated home screen.
3. Retrieve the Firebase multi-factor resolver and display the available enrolled factors.
4. For TOTP, submit the authenticator code through Firebase's TOTP sign-in assertion and resolve the sign-in.
5. Only after the resolver succeeds should the app transition to signed-in state.
6. Force-refresh the ID token and let Nexora verify the Firebase reserved second-factor claim.

### Factor removal and recovery

- Require recent first-factor reauthentication and a second-factor challenge before removing a factor.
- Do not allow removal of the last usable factor without a completed recovery process.
- Never ask support staff to collect a user's TOTP seed or authenticator code.
- Log factor enrollment/removal/recovery events without logging secrets or OTP values.
- Provide an account recovery procedure for users who lose all enrolled factors.

## Backend enforcement

The API currently:
- Verifies Firebase ID tokens with revocation checking.
- Recognizes `firebase.sign_in_second_factor` values `phone` and `totp`.
- Stores MFA verification state on the Nexora session, not as a permanent account-wide boolean.
- Records `identity.mfa_authenticated` once per MFA-authenticated session.
- Exposes the current session's MFA state on `GET /api/v1/account/me/`.
- Provides `VerifiedMFARequired` for views that explicitly require an MFA-authenticated session.

A view that needs MFA must explicitly include both authentication and MFA policy, for example:

```python
from rest_framework.permissions import IsAuthenticated

from apps.identity.permissions import VerifiedMFARequired


class SensitiveOperationView(APIView):
    permission_classes = [IsAuthenticated, VerifiedMFARequired]
```

Do not add this permission to routine account recovery or MFA enrollment endpoints, or users could lock themselves out. For high-impact actions, also define a freshness/step-up policy; an MFA-authenticated session may remain active for a long time.

## Release gates

- [ ] Identity Platform upgrade confirmed for the correct Firebase project.
- [ ] TOTP provider enabled in project configuration.
- [ ] Expo development build can enroll a TOTP factor.
- [ ] Wrong and expired TOTP codes are rejected.
- [ ] MFA-required sign-in is resolved before authenticated navigation.
- [ ] Backend records the second factor from the verified token only.
- [ ] Non-MFA tokens cannot access an MFA-protected test endpoint.
- [ ] Factor removal requires recent reauthentication.
- [ ] Lost-factor recovery has been rehearsed.
- [ ] Abuse limits, monitoring, and support runbooks are active.
- [ ] Production rollout is gradual and reversible.

Until every release gate is satisfied, MFA must be described as an integration foundation, not as an active account protection feature.
