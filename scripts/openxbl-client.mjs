import {
  achievementsFrom,
  firstValue,
  normalizeOpenXblData,
  profilesFrom,
  titleLastPlayed,
  titlesFrom,
} from "./openxbl-normalizer.mjs";

const API_ROOT = "https://xbl.io/api/v2";

async function request(path, apiKey) {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: {
      Accept: "application/json",
      "Accept-Language": "en-US,en",
      "X-Authorization": apiKey,
    },
    signal: AbortSignal.timeout(20000),
    // Never forward the API key to a redirect destination.
    redirect: "error",
  }).catch(() => {
    throw new Error(`OpenXBL ${path} request failed (network error, timeout, or redirect).`);
  });

  if (!response.ok) {
    // Upstream error bodies may contain credentials or personal data.
    await response.body?.cancel().catch(() => {});
    throw new Error(`OpenXBL ${path} returned ${response.status}`);
  }

  try {
    let payload = await response.json();

    for (let depth = 0; depth < 4; depth += 1) {
      if (payload && typeof payload === "object" && "content" in payload) {
        payload = payload.content;
        continue;
      }

      if (typeof payload === "string" && /^[\[{]/.test(payload.trim())) {
        payload = JSON.parse(payload);
        continue;
      }

      if (
        Array.isArray(payload) &&
        payload.length === 1 &&
        typeof payload[0] === "string" &&
        /^[\[{]/.test(payload[0].trim())
      ) {
        payload = JSON.parse(payload[0]);
        continue;
      }

      break;
    }

    return payload;
  } catch {
    // JSON parser errors can include snippets of the response body too.
    throw new Error(`OpenXBL ${path} returned invalid JSON`);
  }
}

export async function fetchOpenXblData(apiKey) {
  const account = await request("/account", apiKey);
  const profile = profilesFrom(account)[0];
  const xuid = firstValue(profile?.id, profile?.xuid);

  if (!xuid) {
    throw new Error(
      "OpenXBL returned no Xbox profile. Confirm the OpenXBL account is linked to Xbox."
    );
  }

  const encodedXuid = encodeURIComponent(String(xuid));
  const titleHistory = await request(
    `/player/titleHistory/${encodedXuid}`,
    apiKey
  );
  const recentTitles = titlesFrom(titleHistory)
    .map((title) => ({ title, lastPlayed: titleLastPlayed(title) }))
    .filter(({ lastPlayed }) => lastPlayed)
    .sort((a, b) => b.lastPlayed.getTime() - a.lastPlayed.getTime())
    .slice(0, 3)
    .map(({ title }) => title);
  const achievementRequests = recentTitles.map(async (title) => {
    const titleId = firstValue(title?.titleId, title?.id);

    if (!titleId) {
      return [];
    }

    try {
      const payload = await request(
        `/achievements/player/${encodedXuid}/${encodeURIComponent(String(titleId))}`,
        apiKey
      );
      return achievementsFrom(payload).map((achievement) =>
        firstValue(
          achievement?.titleAssociations?.[0]?.name,
          achievement?.title?.name,
          achievement?.gameName
        )
          ? achievement
          : { ...achievement, gameName: title?.name || "" }
      );
    } catch {
      // Achievements are optional, including for the most recently played game.
      return [];
    }
  });
  const achievements = {
    achievements: (await Promise.all(achievementRequests)).flat(),
  };

  return normalizeOpenXblData({ account, titleHistory, achievements });
}
