import { Link, useNavigate } from '@tanstack/react-router';
import { LogOut } from 'lucide-react';
import { SearchBox } from '../molecules/SearchBox';
import { Button } from '../atoms/Button';

import DABOJOB_logo from '@/assets/logo/DABOJOB_logo_loop3.gif';

type User = { name: string };

type HeaderProps = {
  user?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;

  fetchSuggestions: (
    q: string,
    signal?: AbortSignal,
  ) => Promise<{ id: string | number; label: string }[]>;
  onSelectSuggestion?: (item: { id: string | number; label: string }) => void;
  onSubmitSearch?: (query: string) => void;
};

export function Header({
  user,
  onLogin,
  onLogout,
  fetchSuggestions,
  onSelectSuggestion,
  onSubmitSearch,
}: HeaderProps) {
  const navigate = useNavigate();

  return (
    <header
      className="
        sticky top-0 z-50 border-b
        bg-white/80 backdrop-blur
        supports-[backdrop-filter]:bg-white/60
      "
    >
      <div className="w-full px-16 py-6">
        <div className="flex h-8 items-center">
          <Logo />

          {/* 검색 영역: SearchBox 항상 표시 */}
          <div className="ml-8 w-[800px]">
            <SearchBox
              fetchSuggestions={fetchSuggestions}
              onSelect={onSelectSuggestion}
              onSubmit={onSubmitSearch}
              className="w-full"
            />
          </div>

          {/* 로그인: 오른쪽 끝 자동 배치 */}
          <div className="ml-auto">
            <UserArea
              user={user}
              onLogin={() => {
                onLogin?.();
                navigate({ to: '/login' });
              }}
              onLogout={onLogout}
            />
          </div>
        </div>
      </div>
    </header>
  );
}

function Logo() {
  return (
    <Link to="/" aria-label="홈으로 이동" className="flex items-center gap-2 shrink-0">
      <img src={DABOJOB_logo} alt="DABOJOB : ) 다보자" className="h-6 w-auto" draggable={false} />
    </Link>
  );
}

function UserArea({
  user,
  onLogin,
  onLogout,
}: {
  user?: User | null;
  onLogin?: () => void;
  onLogout?: () => void;
}) {
  return (
    <div className="flex items-center gap-3 shrink-0">
      {user ? (
        <>
          <span className="hidden sm:block text-sm text-slate-600">{user.name}님 반가워요!</span>
          <Button
            variant="contained"
            size="sm"
            onClick={onLogout}
            startIcon={<LogOut className="h-4 w-4" aria-hidden />}
            aria-label="로그아웃"
          >
            로그아웃
          </Button>
        </>
      ) : (
        <Button variant="contained" size="md" onClick={onLogin} aria-label="로그인">
          로그인
        </Button>
      )}
    </div>
  );
}
