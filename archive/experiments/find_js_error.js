const fs = require('fs');
const html = fs.readFileSync('static/index.html', 'utf8');

const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (!match) {
  console.log("No script tag found.");
  process.exit(1);
}

const jsCode = match[1];
const acorn = require('acorn');

try {
  acorn.parse(jsCode, { ecmaVersion: 2020 });
  console.log("No syntax errors found with Acorn.");
} catch (err) {
  console.log("Acorn Parse Error:", err.message);
  console.log("Location: line", err.loc.line, "column", err.loc.column);
  const lines = jsCode.split('\n');
  console.log("Faulty line:", lines[err.loc.line - 1]);
}
