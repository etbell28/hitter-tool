import { put } from "@vercel/blob";


function unauthorized(response) {
  response.status(401).json({ ok: false, error: "Unauthorized" });
}


export default async function handler(request, response) {
  response.setHeader("Cache-Control", "no-store, max-age=0");

  if (request.method !== "POST") {
    response.status(405).json({ ok: false, error: "Use POST" });
    return;
  }

  const expectedToken = process.env.LIVE_REFRESH_TOKEN;
  if (expectedToken) {
    const receivedToken = request.headers["x-live-refresh-token"];
    if (receivedToken !== expectedToken) {
      unauthorized(response);
      return;
    }
  }

  if (!process.env.BLOB_READ_WRITE_TOKEN) {
    response.status(500).json({
      ok: false,
      error: "Missing BLOB_READ_WRITE_TOKEN"
    });
    return;
  }

  let payload = "";
  for await (const chunk of request) {
    payload += chunk;
    if (payload.length > 5_000_000) {
      response.status(413).json({ ok: false, error: "Payload too large" });
      return;
    }
  }

  try {
    JSON.parse(payload);
  } catch {
    response.status(400).json({ ok: false, error: "Body must be valid JSON" });
    return;
  }

  const blob = await put("live/slate.json", payload, {
    access: "public",
    allowOverwrite: true,
    cacheControlMaxAge: 0,
    contentType: "application/json"
  });

  response.status(200).json({
    ok: true,
    stored: true,
    blobUrl: blob.url
  });
}
