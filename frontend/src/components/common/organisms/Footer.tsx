// components/common/footer/Footer.tsx
import * as React from 'react';

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer aria-label="사이트 푸터" className="w-full bg-daboja-gray-default">
      <div className="mx-auto max-w-6xl px-4 md:px-6">
        <div className="py-10 text-center">
          <p className="text-xs text-slate-500">
            © {year} DABOJOB : ) 다보자 All Rights Reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
