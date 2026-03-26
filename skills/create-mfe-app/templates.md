# MFE App File Templates

All placeholders (`__PLACEHOLDER__`) are replaced by the agent during generation.
See SKILL.md for the substitution table.

---

## 1. `package.json`

```json
{
    "name": "__PACKAGE_NAME__",
    "version": "1.0.0",
    "description": "__APP_DESCRIPTION__",
    "scripts": {
        "start": "webpack serve --mode development",
        "build": "webpack --mode production"
    },
    "dependencies": {
        "react": "^18.2.0",
        "react-dom": "^18.2.0"
    },
    "devDependencies": {
        "@types/react": "^18.2.0",
        "@types/react-dom": "^18.2.0",
        "css-loader": "^6.8.1",
        "html-webpack-plugin": "^5.5.3",
        "style-loader": "^3.3.3",
        "ts-loader": "^9.4.4",
        "typescript": "^5.1.6",
        "webpack": "^5.88.2",
        "webpack-cli": "^5.1.4",
        "webpack-dev-server": "^4.15.1"
    }
}
```

---

## 2. `webpack.config.js`

```js
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = (env, argv) => {
    const isProduction = argv.mode === 'production';
    const publicPath = isProduction
        ? (process.env.MFE_PUBLIC_PATH || 'auto')
        : '__PUBLIC_PATH_DEV__';

    return {
        entry: './src/index.tsx',
        mode: isProduction ? 'production' : 'development',
        devtool: isProduction ? 'source-map' : 'eval-cheap-module-source-map',

        devServer: {
            port: __PORT__,
            hot: true,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
                'Access-Control-Allow-Headers': 'X-Requested-With, content-type, Authorization',
            },
            historyApiFallback: true,
            // {{GRAPHQL_PROXY}}
        },

        output: {
            publicPath,
            path: path.resolve(__dirname, 'dist'),
            filename: isProduction ? '[name].[contenthash].js' : '[name].js',
            clean: true,
        },

        resolve: {
            extensions: ['.tsx', '.ts', '.js', '.jsx'],
        },

        module: {
            rules: [
                {
                    test: /\.(ts|tsx)$/,
                    exclude: /node_modules/,
                    use: {
                        loader: 'ts-loader',
                        options: {
                            transpileOnly: true,
                        },
                    },
                },
                {
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'],
                },
            ],
        },

        plugins: [
            new ModuleFederationPlugin({
                name: '__MF_NAME__',
                filename: 'remoteEntry.js',
                exposes: {
                    './mount': './src/mount.tsx',
                },
                shared: {
                    react: {
                        singleton: true,
                        requiredVersion: '^18.0.0',
                        eager: true,
                    },
                    'react-dom': {
                        singleton: true,
                        requiredVersion: '^18.0.0',
                        eager: true,
                    },
                },
            }),
            new HtmlWebpackPlugin({
                template: './public/index.html',
            }),
        ],

        optimization: {
            splitChunks: false,
        },
    };
};
```

### GraphQL proxy block

When `needs_graphql` is **Yes**, replace the `// {{GRAPHQL_PROXY}}` comment
in the `devServer` section with:

```js
            proxy: [
                {
                    context: ['/api/v2/graphql'],
                    target: 'http://localhost:9002',
                    changeOrigin: true,
                    secure: false,
                },
            ],
```

When `needs_graphql` is **No**, remove the `// {{GRAPHQL_PROXY}}` comment line entirely.

---

## 3. `src/mount.tsx`

```tsx
import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import { App } from './App';

export function mount(container: HTMLElement, _options: Record<string, unknown> = {}): () => void {
    const root: Root = createRoot(container);
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );

    return () => {
        root.unmount();
    };
}

export default mount;
```

---

## 4. `src/index.tsx`

```tsx
import { mount } from './mount';

const rootElement = document.getElementById('root');

if (rootElement) {
    mount(rootElement, {});
}
```

---

## 5. `src/App.tsx`

```tsx
import React from 'react';

const styles: Record<string, React.CSSProperties> = {
    container: {
        fontFamily: "'Segoe UI', 'Roboto', 'Oxygen', sans-serif",
        padding: '24px',
        maxWidth: '800px',
        margin: '0 auto',
    },
    header: {
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '12px',
        padding: '32px',
        color: 'white',
        marginBottom: '24px',
    },
    title: {
        fontSize: '2rem',
        fontWeight: 700,
        margin: 0,
        marginBottom: '8px',
    },
    subtitle: {
        fontSize: '1rem',
        opacity: 0.9,
        margin: 0,
    },
    card: {
        background: '#ffffff',
        borderRadius: '12px',
        padding: '20px',
        marginBottom: '16px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        border: '1px solid #e8e8e8',
    },
};

export const App: React.FC = () => {
    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>__DISPLAY_LABEL__</h1>
                <p style={styles.subtitle}>
                    __APP_DESCRIPTION__
                </p>
            </div>

            <div style={styles.card}>
                <p style={{ color: '#555', lineHeight: 1.6 }}>
                    This MFE is running inside DataHub. Edit <code>src/App.tsx</code> to get started.
                </p>
            </div>
        </div>
    );
};

export default App;
```

---

## 6. `tsconfig.json`

```json
{
    "compilerOptions": {
        "target": "ES2020",
        "lib": ["DOM", "DOM.Iterable", "ESNext"],
        "module": "ESNext",
        "moduleResolution": "node",
        "jsx": "react-jsx",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "forceConsistentCasingInFileNames": true,
        "outDir": "./dist",
        "resolveJsonModule": true,
        "isolatedModules": true
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}
```

---

## 7. `public/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__DISPLAY_LABEL__</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f5f5f5;
        }
        #root {
            min-height: 100vh;
        }
    </style>
</head>
<body>
    <div id="root"></div>
</body>
</html>
```
