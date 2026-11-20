# Newsletter / Smart Link — Simon Libon

## What is configured

- `listen.html?preview=1` is a safe interactive *visual preview*: it lists platforms without pretending any track exists. The main site menu does not change.
- `listen.html?id=release-slug` uses entries in `releases.json`. It only displays entries marked `published: true` with valid HTTPS streaming URLs.
- `email-templates/new-release.html` matches the site's light palette, small social icons and button, and includes an EmailOctopus unsubscribe merge tag.
- `{{UnsubscribeURL}}` is **recipient-specific** and only works in EmailOctopus campaigns. Gmail sends must not use this unresolved placeholder. `{{SenderInfo}}` is required; `{{RewardsURL}}` is required on the free Starter plan.
- In the email template, the `LISTEN NOW` button currently links to the **preview**. Before sending a real announcement, replace that with the correct published `?id=release-slug` page and replace the title, format and artwork.
- No contacts were subscribed or unsubscribed and **no sending automation is enabled by these files**.

## How to add an actual release

Edit `releases.json`, filling in the real cover and confirmed direct track/EP/album links. Do not link to an artist profile in place of a specific release:

```json
{
  "releases": [
    {
      "id": "release-slug",
      "title": "Release title",
      "type": "single",
      "cover": "https://your-cdn.example/actual-cover.jpg",
      "published": false,
      "platforms": [
        {"name":"Spotify","url":"https://open.spotify.com/track/actual-id"},
        {"name":"Apple Music","url":"https://music.apple.com/actual-track-id"}
      ]
    }
  ]
}
```

After the release is genuinely live, set `published:true`, test `listen.html?id=release-slug`, then update the newsletter's button URL. EmailOctopus must manage recipients' `{{UnsubscribeURL}}`. A direct Gmail test does not provide a subscriber-specific opt-out link.
