export function firstValue(...values) {
  return values.find((value) => value !== undefined && value !== null && value !== "");
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function safeDate(value) {
  const parsed = value ? new Date(value) : null;
  return parsed && !Number.isNaN(parsed.getTime()) ? parsed : null;
}

function safeImageUrl(value) {
  if (typeof value !== "string" || !value.trim()) {
    return null;
  }

  try {
    const url = new URL(value.replace(/^http:/, "https:"));
    return url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function imageFrom(value) {
  if (typeof value === "string") {
    return safeImageUrl(value);
  }

  if (!value || typeof value !== "object") {
    return null;
  }

  return safeImageUrl(firstValue(value.url, value.uri, value.imageUrl));
}

function relativeLabel(value, now = new Date()) {
  const date = safeDate(value);

  if (!date) {
    return null;
  }

  const minutes = Math.max(0, Math.floor((now.getTime() - date.getTime()) / 60000));

  if (minutes < 1) {
    return "just now";
  }

  if (minutes < 60) {
    return `${minutes}m ago`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }

  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `${days}d ago`;
  }

  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
  }).format(date);
}

function settingsMap(profile) {
  return Object.fromEntries(
    asArray(profile?.settings)
      .filter((setting) => setting?.id)
      .map((setting) => [setting.id, setting.value])
  );
}

export function titlesFrom(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return asArray(firstValue(payload?.titles, payload?.titleHistory?.titles, payload?.items));
}

export function achievementsFrom(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return asArray(
    firstValue(
      payload?.achievements,
      payload?.achievementList,
      payload?.items,
      payload?.results
    )
  );
}

export function profilesFrom(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }

  const nested = asArray(
    firstValue(payload?.profileUsers, payload?.people, payload?.results, payload?.items)
  );

  if (nested.length) {
    return nested;
  }

  return payload && typeof payload === "object" && (payload.xuid || payload.id)
    ? [payload]
    : [];
}

export function titleLastPlayed(title) {
  return safeDate(
    firstValue(
      title?.titleHistory?.lastTimePlayed,
      title?.titleHistory?.lastPlayed,
      title?.lastTimePlayed,
      title?.lastPlayedAt
    )
  );
}

function titleImage(title) {
  const images = asArray(firstValue(title?.images, title?.mediaAssets));
  return firstValue(
    safeImageUrl(title?.displayImage),
    safeImageUrl(title?.imageUrl),
    safeImageUrl(title?.titleImage),
    images.map(imageFrom).find(Boolean)
  );
}

function achievementUnlockedAt(achievement) {
  return safeDate(
    firstValue(
      achievement?.progression?.timeUnlocked,
      achievement?.timeUnlocked,
      achievement?.unlockTime,
      achievement?.dateUnlocked,
      achievement?.unlockedAt
    )
  );
}

function achievementImage(achievement) {
  const media = asArray(firstValue(achievement?.mediaAssets, achievement?.images));
  const icon = media.find((asset) => {
    const type = String(firstValue(asset?.type, asset?.name, asset?.purpose) || "");
    return /icon|achievement/i.test(type);
  });

  return firstValue(
    imageFrom(icon),
    media.map(imageFrom).find(Boolean),
    safeImageUrl(achievement?.imageUrl),
    safeImageUrl(achievement?.icon)
  );
}

function achievementGamerscore(achievement) {
  const rewards = asArray(achievement?.rewards);
  const reward = rewards.find((item) => {
    const type = String(firstValue(item?.type, item?.name) || "");
    return /gamerscore/i.test(type);
  });
  const raw = firstValue(
    reward?.value,
    reward?.valueString,
    achievement?.gamerscore,
    achievement?.score
  );
  const score = Number.parseInt(String(raw || ""), 10);
  return Number.isFinite(score) ? score : null;
}

function isUnlocked(achievement) {
  const state = String(firstValue(achievement?.progressState, achievement?.state) || "");
  return /achieved|unlocked/i.test(state) || Boolean(achievementUnlockedAt(achievement));
}

export function normalizeOpenXblData(
  { account, titleHistory, achievements },
  now = new Date()
) {
  const profile = profilesFrom(account)[0];

  if (!profile) {
    throw new Error("OpenXBL returned no Xbox profile.");
  }

  const settings = settingsMap(profile);
  const gamertag = String(
    firstValue(settings.Gamertag, profile.gamertag) || ""
  ).trim();

  if (!gamertag) {
    throw new Error("OpenXBL returned a profile without a gamertag.");
  }

  const recentTitle = titlesFrom(titleHistory)
    .map((title) => ({ title, lastPlayed: titleLastPlayed(title) }))
    .filter(({ lastPlayed }) => lastPlayed)
    .sort((a, b) => b.lastPlayed.getTime() - a.lastPlayed.getTime())[0];

  const latestAchievement = achievementsFrom(achievements)
    .filter(isUnlocked)
    .map((achievement) => ({
      achievement,
      unlockedAt: achievementUnlockedAt(achievement),
    }))
    .filter(({ unlockedAt }) => unlockedAt)
    .sort((a, b) => b.unlockedAt.getTime() - a.unlockedAt.getTime())[0];

  const activityDate = [recentTitle?.lastPlayed, latestAchievement?.unlockedAt]
    .filter(Boolean)
    .sort((a, b) => b.getTime() - a.getTime())[0];
  const gamerScore = Number.parseInt(
    String(firstValue(settings.Gamerscore, profile.gamerscore) || ""),
    10
  );
  const profileUrl = `https://account.xbox.com/en-us/Profile?gamertag=${encodeURIComponent(
    gamertag
  )}`;

  const result = {
    profile: {
      xuid: String(firstValue(profile.id, profile.xuid) || ""),
      gamertag,
      gamerscore: Number.isFinite(gamerScore) ? gamerScore : null,
      gamerscoreLabel: Number.isFinite(gamerScore)
        ? new Intl.NumberFormat("en").format(gamerScore)
        : null,
      avatarUrl: safeImageUrl(
        firstValue(
          settings.GameDisplayPicRaw,
          settings.GameDisplayPic,
          profile.displayPicRaw,
          profile.profilePicture,
          profile.avatarUrl
        )
      ),
      profileUrl,
      activityLabel: relativeLabel(activityDate, now),
    },
    game: recentTitle
      ? {
          id: String(
            firstValue(recentTitle.title?.titleId, recentTitle.title?.id, "") || ""
          ),
          name: String(
            firstValue(
              recentTitle.title?.name,
              recentTitle.title?.titleName,
              recentTitle.title?.displayName,
              "Unknown game"
            )
          ).trim(),
          imageUrl: titleImage(recentTitle.title),
          lastPlayedAt: recentTitle.lastPlayed.toISOString(),
          lastPlayedLabel: relativeLabel(recentTitle.lastPlayed, now),
        }
      : null,
    achievement: latestAchievement
      ? {
          id: String(
            firstValue(
              latestAchievement.achievement?.id,
              latestAchievement.achievement?.achievementId,
              ""
            ) || ""
          ),
          name: String(
            firstValue(
              latestAchievement.achievement?.name,
              latestAchievement.achievement?.displayName,
              "Achievement unlocked"
            )
          ).trim(),
          gameName: String(
            firstValue(
              latestAchievement.achievement?.titleAssociations?.[0]?.name,
              latestAchievement.achievement?.title?.name,
              latestAchievement.achievement?.gameName,
              ""
            ) || ""
          ).trim(),
          imageUrl: achievementImage(latestAchievement.achievement),
          gamerscore: achievementGamerscore(latestAchievement.achievement),
          unlockedAt: latestAchievement.unlockedAt.toISOString(),
          unlockedLabel: relativeLabel(latestAchievement.unlockedAt, now),
        }
      : null,
    updatedAt: now.toISOString(),
    updatedLabel: "Updated today",
    source: "OpenXBL",
  };

  if (!result.game) {
    throw new Error(
      "OpenXBL returned no recently played game. Check Xbox profile privacy settings."
    );
  }

  return result;
}
