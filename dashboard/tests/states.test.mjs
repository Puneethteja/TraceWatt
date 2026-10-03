import test, { before, after } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "vite";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
let server, UI;
before(async () => {
  server = await createServer({
    server: { middlewareMode: true },
    appType: "custom",
  });
  UI = await server.ssrLoadModule("/src/components/UI.jsx");
});
after(async () => {
  await server?.close();
});
test("empty consumer state contains no invented records", () => {
  const html = renderToStaticMarkup(
    createElement(
      UI.Resource,
      {
        resource: { data: [], loading: false, error: null },
        empty: "No consumers found",
      },
      () => {
        throw Error("Empty state must not render records");
      },
    ),
  );
  assert.match(html, /No consumers found/);
});
test("loading state provides an accessible skeleton", () => {
  const html = renderToStaticMarkup(
    createElement(UI.Resource, { resource: { loading: true } }, () => null),
  );
  assert.match(html, /role="status"/);
  assert.match(html, /Loading data/);
});
test("unavailable analysis pipeline never claims that detection completed", () => {
  const html = renderToStaticMarkup(createElement(UI.Pipeline, {}));
  assert.match(html, /ML unavailable/);
  assert.match(html, /Not observed/);
  assert.doesNotMatch(html, /Detection available|Healthy|Processing/);
});
test("failed refresh hides prior records and offers retry", () => {
  const html = renderToStaticMarkup(
    createElement(
      UI.Resource,
      {
        resource: {
          data: [],
          error: new Error("Connection unavailable"),
          loading: false,
          refresh: () => {},
        },
      },
      () => {
        throw Error("Failed request must not render data");
      },
    ),
  );
  assert.match(html, /Connection unavailable/);
  assert.match(html, /Retry/);
});
