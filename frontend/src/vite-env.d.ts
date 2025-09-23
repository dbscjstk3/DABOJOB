/// <reference types="vite/client" />

declare module '*?format=webp&quality=80' {
  const src: string;
  export default src;
}

declare module '*?format=webp' {
  const src: string;
  export default src;
}

declare module 'vite-imagetools' {
  import { Plugin } from 'vite';

  interface ImagetoolsOptions {
    include?: RegExp | string | string[];
    exclude?: RegExp | string | string[];
    defaultDirectives?: (url: URL) => URLSearchParams;
  }

  function imagetools(options?: ImagetoolsOptions): Plugin;

  export { imagetools };
}
