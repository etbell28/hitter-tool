export default async function handler(request, response) {
  response.setHeader("Cache-Control", "no-store, max-age=0");
  response.status(200).json({
    ok: true,
    message: "Refresh computation runs in GitHub Actions on the free setup. The action posts finished JSON to /api/update-slate."
  });
}
