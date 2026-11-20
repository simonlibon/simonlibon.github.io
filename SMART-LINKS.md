# Smart Link — streaming release pages

This is a standalone page; the existing site's navigation is unchanged.

The link for a release is \`https://simonlibon.github.io/listen.html?id=release-slug\`.

Before a newsletter goes out, add a release object to \`releases.json\`, with a unique lower-case hyphenated \`id\`, real title, cover URL, and verified direct URLs to **the specific single, EP, or album**, not the artist profile. Mark it \`published: true\` only when the release can be streamed.

Example structure (illustrative, not real links):

\`\`\`json
{
  "releases": [
    {
      "id": "my-single",
      "title": "My Single",
      "type": "single",
      "cover": "https://example.com/my-single-cover.jpg",
      "published": false,
      "platforms": [
        {"name": "Spotify", "url": "https://open.spotify.com/track/..."},
        {"name": "Apple Music", "url": "https://music.apple.com/..."}
      ]
    }
  ]
}
\`\`\`

The \`releases.json\` file intentionally starts empty so no fake release or unverified link is published. A newsletter must only link to the page **after** this data is published and the destination URLs tested. Gmail/Outlook will open the page rather than an in-email popover.

This page handles no subscriptions or mass email sending.
