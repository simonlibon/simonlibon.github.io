# Release newsletter drafts

This folder contains the existing EmailOctopus HTML design and, when new releases are published, generated email drafts.

## How it works
1. Add a release to `releases.json` with a unique lowercase `id`, `title`, `type` (`single`, `ep`, `album`), HTTPS `cover`, and at least one HTTPS listening link in `platforms`.
2. Change `published` to `true` only when the music is actually live and its listening links work.
3. GitHub Actions runs `scripts/prepare_release_newsletters.py`, creating `email-templates/drafts/<id>.html` and `<id>.json` using the existing site design. The JSON contains the suggested email subject, preview text and link.
4. Review the generated email and send it from EmailOctopus only after a test email succeeds. The email template includes the EmailOctopus unsubscribe and sender-information merge tags.

## Important
**Nothing here sends email.** EmailOctopus does not offer an official API endpoint for creating/sending campaigns; the API can trigger an automation configured in its dashboard. A genuine end-to-end sender requires separate setup and a real test. Never place API keys, subscriber data or sensitive information in this public repository.

Publishing a release on DistroKid/Spotify alone does not update this JSON file. This workflow detects changes to **your own `releases.json`**, not external music platforms. A draft appearing is not proof that an email was delivered.

For the future custom domain, change the `SITE_BASE_URL` environment variable in the workflow after HTTPS and redirects are working.
