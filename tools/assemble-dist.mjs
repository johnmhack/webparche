import { cpSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

cpSync(join(root, 'apps', 'landing'), dist, { recursive: true });
cpSync(join(root, 'apps', 'revista'), join(dist, 'revista'), { recursive: true });

execSync('npm run build', { cwd: join(root, 'apps', 'torker'), stdio: 'inherit' });

if (!existsSync(join(dist, 'torker', 'index.html'))) {
  console.error('Build Torker no generó dist/torker/index.html');
  process.exit(1);
}

console.log('OK dist/ → landing + revista + torker');
