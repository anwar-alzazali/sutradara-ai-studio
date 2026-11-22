// node --test bot/
import test from "node:test";
import assert from "node:assert/strict";
import { bacaTombol, tombolPersetujuan, tombolAlasan, tombolSesudah, idAman, catatanKeputusan, bolehAkses, ALASAN } from "./worker.js";

test("tombol persetujuan dapat dibaca balik dan muat batas 64 byte Telegram", () => {
  const id = idAman("2026-11-21 Nuh Mengejek / versi 2");
  for (const b of [...tombolPersetujuan(id).flat(), ...tombolAlasan(id).flat()]) {
    assert.ok(new TextEncoder().encode(b.callback_data).length <= 64);
    assert.ok(bacaTombol(b.callback_data));
  }
  assert.deepEqual(bacaTombol(`st:${id}`), { aksi: "st", id, alasan: null });
  assert.deepEqual(bacaTombol(`al:${id}:hook`), { aksi: "al", id, alasan: "hook" });
});

test("data tombol asing atau berbahaya ditolak", () => {
  for (const d of ["", "x", "nom:10000", "st:../../etc", "al:abc:ngawur", "st:A B", "uji:ok"]) assert.equal(bacaTombol(d), null, d);
});

test("catatan keputusan berisi alasan yang terbaca", () => {
  const c = catatanKeputusan("nuh-1", "ditolak", "visual", null, "2026-11-21T00:00:00Z");
  assert.equal(c.alasan, ALASAN.visual); assert.equal(c.kode_alasan, "visual"); assert.equal(c.keputusan, "ditolak");
});

test("hanya pemilik yang boleh memakai bot", () => {
  assert.ok(bolehAkses({ TELEGRAM_CHAT_ID: "123\n" }, 123));
  assert.ok(!bolehAkses({ TELEGRAM_CHAT_ID: "123" }, 456));
});

test("keputusan bisa diubah dan keputusan lama tersimpan di riwayat", () => {
  const id = "nuh-1";
  const ub = tombolSesudah(id, "✅ Disetujui").flat().find((b) => b.callback_data.startsWith("ub:"));
  assert.deepEqual(bacaTombol(ub.callback_data), { aksi: "ub", id, alasan: null });
  const a = catatanKeputusan(id, "disetujui", null, null, "t1");
  const b = catatanKeputusan(id, "ditolak", "hook", null, "t2", a);
  const c = catatanKeputusan(id, "disetujui", null, null, "t3", b);
  assert.equal(c.keputusan, "disetujui");
  assert.deepEqual(c.riwayat.map((r) => r.keputusan), ["disetujui", "ditolak"]);
  assert.equal(c.riwayat[1].alasan, ALASAN.hook);
  assert.equal(a.riwayat, undefined);
});

import { readFileSync } from "node:fs";
import { kartuStatus, tombolKartu, idAntrean, statusBaru } from "./worker.js";

test("kartu status bot identik dengan versi Python (fixture bersama)", () => {
  const f = JSON.parse(readFileSync(new URL("../tests/data/kartu_status.json", import.meta.url)));
  assert.equal(kartuStatus(f.status), f.teks);
  assert.ok(tombolKartu(f.status).flat().some((b) => b.callback_data === `nl:${f.status.id}`));
});

test("id antrean aman, pendek, dan tombolnya terbaca", () => {
  const id = idAntrean("Nabi Hud dan Kaum 'Ad — azab angin", new Date("2026-11-21T09:05:00Z"));
  assert.equal(id, "261121-1605-nabi-hud-dan-kaum");
  for (const a of ["nl", "nr", "nb"]) assert.deepEqual(bacaTombol(`${a}:${id}`), { aksi: a, id, alasan: null });
  const st = statusBaru(id, "x", "ide", 1);
  assert.equal(st.tahap.diterima, "jalan");
  assert.ok(tombolKartu(st).flat().every((b) => b.callback_data === "menu"));
});

import { keGemini, pilihModelGemini, labelBiaya } from "./worker.js";

test("pesan format Claude diubah ke format Gemini (teks, gambar, peran)", () => {
  const g = keGemini("sistem", [
    { role: "user", content: [{ type: "image", source: { type: "base64", media_type: "image/jpeg", data: "QUJD" } }, { type: "text", text: "balas" }] },
    { role: "assistant", content: "oke" },
  ]);
  assert.equal(g.systemInstruction.parts[0].text, "sistem");
  assert.deepEqual(g.contents[0].parts[0], { inline_data: { mime_type: "image/jpeg", data: "QUJD" } });
  assert.equal(g.contents[0].parts[1].text, "balas");
  assert.equal(g.contents[1].role, "model");
});

test("model Gemini: dua flash terbaru lalu satu lite", () => {
  assert.deepEqual(pilihModelGemini(["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro", "gemini-3.0-flash", "gemini-2.0-flash-lite"]),
    ["gemini-3.0-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite"]);
});

test("label biaya menandai penyedia", () => {
  assert.equal(labelBiaya({ idr: 0, model: "gemini-2.5-flash" }), "Rp0 · Gemini");
  assert.equal(labelBiaya({ idr: 12, model: "claude-sonnet-4-5" }), "≈Rp12 · Claude");
});
