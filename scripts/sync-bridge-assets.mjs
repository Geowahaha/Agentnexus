import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const assetsDir = path.join(root, 'frontend/public/bridge/assets')
const wsSrc = path.join(root, 'packages/bridge/node_modules/ws')
const wsDest = path.join(assetsDir, 'node_modules/ws')
const bundleZip = path.join(root, 'frontend/public/bridge/bridge-bundle.zip')

fs.mkdirSync(assetsDir, { recursive: true })
fs.copyFileSync(path.join(root, 'packages/bridge/index.mjs'), path.join(assetsDir, 'index.mjs'))
fs.copyFileSync(path.join(root, 'packages/bridge/package.json'), path.join(assetsDir, 'package.json'))

fs.rmSync(wsDest, { recursive: true, force: true })
if (fs.existsSync(wsSrc)) {
  fs.mkdirSync(path.dirname(wsDest), { recursive: true })
  if (process.platform === 'win32') {
    execSync(`xcopy "${wsSrc}" "${wsDest}" /E /I /Y`, { stdio: 'inherit' })
  } else {
    execSync(`cp -R "${wsSrc}" "${wsDest}"`)
  }
}

if (fs.existsSync(bundleZip)) fs.unlinkSync(bundleZip)
if (process.platform === 'win32') {
  execSync(
    `powershell -NoProfile -Command "Compress-Archive -Path '${assetsDir}\\*' -DestinationPath '${bundleZip}' -Force"`,
    { stdio: 'inherit' },
  )
} else {
  execSync(`cd "${assetsDir}" && zip -r "${bundleZip}" .`, { stdio: 'inherit' })
}

console.log('Bridge assets synced:', assetsDir)
console.log('Bundle:', bundleZip)