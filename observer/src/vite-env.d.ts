/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_ECP_BASE_URL?: string;
  readonly VITE_ECP_API_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
