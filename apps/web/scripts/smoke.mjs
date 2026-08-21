const baseUrl = process.env.WEB_BASE_URL ?? "http://localhost:3000";
const response = await fetch(baseUrl);

if (!response.ok) {
  throw new Error(`Web smoke failed with HTTP ${response.status}`);
}

const html = await response.text();
for (const expected of ["시작하기", "광고 소재 분석 도구", "우리 브랜드와 경쟁사의 광고 소재"]) {
  if (!html.includes(expected)) {
    throw new Error(`Web smoke response is missing: ${expected}`);
  }
}

console.log(`Web smoke passed: ${baseUrl}`);
