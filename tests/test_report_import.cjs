const test = require("node:test");
const assert = require("node:assert/strict");
const { parseCsv, parseJson, MAX_BYTES, MAX_ROWS } = require("../src/report_interactions.js");

const header = "package_name,name,category,sub_category,installation_count,average_score,comment_count,version,last_update,source";
function fixture(name) {
  const escaped = (name || "Example").replace(/"/g, '""');
  return 'ir.example.app,"' + escaped + '",Tools,Utilities,1250,4.5,12,1.2,2026-10-01,MYKET';
}

test("parses crawler CSV quoting, escaped quotes and CRLF", () => {
  const records = parseCsv("\uFEFF" + header + "\r\n" + fixture('A, "Quoted"'));
  assert.equal(records.length, 1);
  assert.equal(records[0].name, 'A, "Quoted"');
  assert.equal(records[0].installation_count, 1250);
});

test("parses supported JSON arrays and records envelope", () => {
  const record = { package_name: "ir.example.app", name: "<img src=x onerror=1>", category: "Tools", installation_count: 0, average_score: 0, version: "", last_update: "" };
  assert.equal(parseJson(JSON.stringify([record]))[0].name, record.name);
  assert.equal(parseJson(JSON.stringify({ records: [record] })).length, 1);
});

test("rejects invalid schema, malformed CSV, invalid numbers and duplicate headers", () => {
  assert.throws(() => parseCsv("name,category\nOnly,Tools"), /ستون لازم/);
  assert.throws(() => parseCsv(header + "\n" + fixture().replace("1250", "-1")), /عدد نامعتبر/);
  assert.throws(() => parseCsv(header + ",name\n" + fixture() + ",x"), /تکراری/);
  assert.throws(() => parseCsv(header + "\n" + fixture().replace("Example", '"unterminated')), /نقل‌قول/);
  assert.throws(() => parseJson('{"unexpected": []}'), /باید آرایه/);
});

test("accepts empty report state and enforces row and byte caps", () => {
  assert.deepEqual(parseCsv(header), []);
  assert.throws(() => parseCsv("x".repeat(MAX_BYTES + 1)), /۵ مگابایت/);
  const tooMany = Array.from({ length: MAX_ROWS + 1 }, () => ({ package_name: "ir.x", name: "x", category: "c", installation_count: 0, average_score: 0, version: "", last_update: "" }));
  assert.throws(() => parseJson(JSON.stringify(tooMany)), /۵۰۰۰/);
});
