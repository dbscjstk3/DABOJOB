import { Outlet } from '@tanstack/react-router';

export function RootLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b"></header>
      <main className="w-full flex-1">
        <Outlet />
      </main>
      <footer className="border-t">
        <div className="mx-auto max-w-5xl p-4 text-sm text-slate-500">© 2025</div>
      </footer>
    </div>
  );
}
