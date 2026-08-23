import test from "node:test";
import assert from "node:assert/strict";

import {
  fetchOpenXblData,
  normalizeOpenXblData,
} from "./fetch-openxbl.mjs";

test("normalizes the latest Xbox activity for the compact now-page component", () => {
  const now = new Date("2026-07-28T12:00:00.000Z");
  const result = normalizeOpenXblData(
    {
      account: {
        profileUsers: [
          {
            id: "12345",
            settings: [
              { id: "Gamertag", value: "Cherry Sando" },
              { id: "Gamerscore", value: "78560" },
              {
                id: "GameDisplayPicRaw",
                value: "http://images-eds-ssl.xboxlive.com/avatar.png",
              },
            ],
          },
        ],
      },
      titleHistory: {
        titles: [
          {
            titleId: "old",
            name: "Older Game",
            displayImage: "https://example.com/old.png",
            titleHistory: { lastTimePlayed: "2026-07-25T10:00:00.000Z" },
          },
          {
            titleId: "new",
            name: "Starfield",
            displayImage: "https://example.com/starfield.png",
            titleHistory: { lastTimePlayed: "2026-07-28T10:00:00.000Z" },
          },
        ],
      },
      achievements: {
        achievements: [
          {
            id: "locked",
            name: "Not yet",
            progressState: "InProgress",
          },
          {
            id: "unlocked",
            name: "The Long Way Around",
            progressState: "Achieved",
            progression: { timeUnlocked: "2026-07-28T09:30:00.000Z" },
            titleAssociations: [{ name: "Starfield" }],
            mediaAssets: [
              { name: "Icon", url: "https://example.com/achievement.png" },
            ],
            rewards: [{ name: "Gamerscore", value: "15" }],
          },
        ],
      },
    },
    now
  );

  assert.equal(result.profile.gamertag, "Cherry Sando");
  assert.equal(result.profile.gamerscoreLabel, "78,560");
  assert.equal(
    result.profile.avatarUrl,
    "https://images-eds-ssl.xboxlive.com/avatar.png"
  );
  assert.equal(result.game.name, "Starfield");
  assert.equal(result.game.lastPlayedLabel, "2h ago");
  assert.equal(result.achievement.name, "The Long Way Around");
  assert.equal(result.achievement.gamerscore, 15);
  assert.equal(result.profile.activityLabel, "2h ago");
});

test("rejects private title history instead of publishing an empty card", () => {
  assert.throws(
    () =>
      normalizeOpenXblData({
        account: {
          profileUsers: [
            {
              id: "12345",
              settings: [{ id: "Gamertag", value: "Cherry Sando" }],
            },
          ],
        },
        titleHistory: { titles: [] },
        achievements: { achievements: [] },
      }),
    /privacy settings/
  );
});

test("fetches and unwraps OpenXBL data while tolerating older-title failures", async (t) => {
  const originalFetch = globalThis.fetch;
  const requests = [];

  t.after(() => {
    globalThis.fetch = originalFetch;
  });

  globalThis.fetch = async (url, options) => {
    const path = new URL(url).pathname;
    requests.push({ path, options });

    const responses = {
      "/api/v2/account": {
        content: JSON.stringify({
          profileUsers: [
            {
              id: "12345",
              settings: [
                { id: "Gamertag", value: "Cherry Sando" },
                { id: "Gamerscore", value: "78560" },
              ],
            },
          ],
        }),
      },
      "/api/v2/player/titleHistory/12345": {
        titles: [
          {
            titleId: "new",
            name: "Starfield",
            titleHistory: { lastTimePlayed: "2026-07-28T10:00:00.000Z" },
          },
          {
            titleId: "old",
            name: "Older Game",
            titleHistory: { lastTimePlayed: "2026-07-25T10:00:00.000Z" },
          },
        ],
      },
      "/api/v2/achievements/player/12345/new": {
        achievements: [
          {
            id: "unlocked",
            name: "The Long Way Around",
            progressState: "Achieved",
            progression: { timeUnlocked: "2026-07-28T09:30:00.000Z" },
          },
        ],
      },
    };

    if (path.endsWith("/old")) {
      return {
        ok: false,
        status: 503,
        async text() {
          return "temporarily unavailable";
        },
      };
    }

    return {
      ok: true,
      status: 200,
      async json() {
        return responses[path];
      },
    };
  };

  const result = await fetchOpenXblData("secret-key");

  assert.deepEqual(
    requests.map(({ path }) => path),
    [
      "/api/v2/account",
      "/api/v2/player/titleHistory/12345",
      "/api/v2/achievements/player/12345/new",
      "/api/v2/achievements/player/12345/old",
    ]
  );
  assert.ok(
    requests.every(
      ({ options }) => options.headers["X-Authorization"] === "secret-key"
    )
  );
  assert.equal(result.profile.gamertag, "Cherry Sando");
  assert.equal(result.game.name, "Starfield");
  assert.equal(result.achievement.name, "The Long Way Around");
});
