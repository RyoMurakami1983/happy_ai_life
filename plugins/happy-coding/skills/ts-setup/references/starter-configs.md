# TypeScript セットアップの設定例

`SKILL.md` を短く保つため、具体例はここにまとめます。

## TypeScript

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ES2020",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "rootDir": "./src",
    "outDir": "./dist",
    "declaration": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

ES Modules を使うなら、相対 import は `.js` 拡張子付きで書きます。

```typescript
import { MyClass } from './MyClass.js';
```

## ESLint / Prettier

### 依存追加

```powershell
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
```

### `.eslintrc.cjs`

```javascript
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended', 'prettier'],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module'
  },
  env: {
    node: true,
    es2020: true
  },
  rules: {
    '@typescript-eslint/explicit-function-return-type': 'warn',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
  }
};
```

### `.prettierrc`

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

## Jest

### 依存追加

```powershell
npm install --save-dev jest ts-jest @types/jest
```

### `jest.config.cjs`

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts', '!src/**/*.d.ts']
};
```

### `package.json` scripts

```json
{
  "scripts": {
    "build": "tsc",
    "lint": "eslint src/ --ext .ts",
    "format": "prettier --write src/",
    "test": "jest"
  }
}
```

## VS Code

### `.vscode/settings.json`

```json
{
  "[typescript]": {
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.codeActionsOnSave": {
      "source.fixAll.eslint": "explicit"
    }
  },
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

### `.vscode/extensions.json`

```json
{
  "recommendations": [
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

## Quality gates

- `format`: 書式をそろえる
- `lint`: 静的解析を通す
- `build`: `tsc` で型チェックと出力確認をする
- `test`: 振る舞いの回帰を確認する

## Verification

```powershell
npm ci
npm run format
npm run lint
npm run build
npm run test
```
